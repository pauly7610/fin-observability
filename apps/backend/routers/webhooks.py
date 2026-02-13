"""
Webhook ingestion endpoints for external data sources.

External systems (Plaid, Stripe, bank feeds, etc.) push transactions here.
Each transaction is scored by the ML compliance engine, stored with results,
and traced via OpenTelemetry.

Features:
- Inbound webhook ingestion (single + batch up to 10,000)
- SSE streaming endpoint for real-time compliance decisions
- Outbound webhook notifications with retry + dead letter queue
- Scheduled pull ingestion from configured external APIs
- Results retrieval with filtering

Authentication: API key via X-Webhook-Key header or ?key= query param.
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from opentelemetry import trace
from collections import deque
import asyncio
import hashlib
import hmac
import httpx
import json
import os
import logging
import threading
import time
import uuid

from ..database import get_db, SessionLocal
from ..models import Transaction as TransactionModel
from ..ml.anomaly_detector import get_detector
from ..pii_utils import hash_pii_in_dict
from ..key_utils import get_or_generate_key

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)
tracer = trace.get_tracer("webhooks")


# ---------------------------------------------------------------------------
# SSE Event Bus — broadcasts scored results to all connected SSE clients
# ---------------------------------------------------------------------------
class EventBus:
    """Simple pub/sub for SSE streaming. Thread-safe."""

    def __init__(self):
        self._subscribers: list[asyncio.Queue] = []
        self._lock = threading.Lock()
        self._recent: deque = deque(maxlen=50)  # last 50 events for replay

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=256)
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        with self._lock:
            try:
                self._subscribers.remove(q)
            except ValueError:
                pass

    def publish(self, event: dict):
        self._recent.append(event)
        with self._lock:
            dead = []
            for q in self._subscribers:
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    dead.append(q)
            for q in dead:
                try:
                    self._subscribers.remove(q)
                except ValueError:
                    pass

    def get_recent(self) -> list:
        return list(self._recent)

    @property
    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)


event_bus = EventBus()


# ---------------------------------------------------------------------------
# Outbound Webhook Notifications — POST flagged results to callback URLs
# ---------------------------------------------------------------------------
class OutboundNotifier:
    """
    When a transaction is flagged (manual_review), POST the result to
    all registered callback URLs. Retries up to 3 times with exponential
    backoff. Failed deliveries go to a dead letter queue.
    """

    def __init__(self):
        self._callbacks: list[str] = []
        self._dead_letter: deque = deque(maxlen=1000)
        self._delivery_log: deque = deque(maxlen=500)
        self._lock = threading.Lock()
        self._load_callbacks()

    def _load_callbacks(self):
        """Load callback URLs from WEBHOOK_CALLBACK_URLS env var (comma-separated)."""
        raw = os.getenv("WEBHOOK_CALLBACK_URLS", "")
        if raw.strip():
            self._callbacks = [u.strip() for u in raw.split(",") if u.strip()]
            logger.info(f"Outbound webhooks configured: {len(self._callbacks)} callback(s)")

    def register_callback(self, url: str):
        with self._lock:
            if url not in self._callbacks:
                self._callbacks.append(url)

    def remove_callback(self, url: str):
        with self._lock:
            try:
                self._callbacks.remove(url)
            except ValueError:
                pass

    def list_callbacks(self) -> list[str]:
        with self._lock:
            return list(self._callbacks)

    def get_dead_letter(self, limit: int = 50) -> list:
        return list(self._dead_letter)[-limit:]

    def get_delivery_log(self, limit: int = 50) -> list:
        return list(self._delivery_log)[-limit:]

    async def notify(self, result: dict):
        """Send flagged result to all callbacks. Non-blocking."""
        if not self._callbacks:
            return
        # Only notify on flagged transactions
        if result.get("decision") != "manual_review":
            return

        payload = {
            "event": "transaction.flagged",
            "timestamp": datetime.utcnow().isoformat(),
            "data": result,
        }

        for url in self._callbacks:
            asyncio.create_task(self._deliver(url, payload))

    async def _deliver(self, url: str, payload: dict, max_retries: int = 3):
        """Deliver with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        url,
                        json=payload,
                        headers={"Content-Type": "application/json", "User-Agent": "fin-observability/webhook"},
                    )
                    if resp.status_code < 300:
                        self._delivery_log.append({
                            "url": url,
                            "status": resp.status_code,
                            "attempt": attempt + 1,
                            "timestamp": datetime.utcnow().isoformat(),
                            "transaction_id": payload["data"].get("transaction_id"),
                        })
                        return
                    logger.warning(f"Outbound webhook {url} returned {resp.status_code}, attempt {attempt + 1}")
            except Exception as e:
                logger.warning(f"Outbound webhook {url} failed: {e}, attempt {attempt + 1}")

            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s

        # All retries exhausted → dead letter queue
        self._dead_letter.append({
            "url": url,
            "payload": payload,
            "failed_at": datetime.utcnow().isoformat(),
            "attempts": max_retries,
        })
        logger.error(f"Outbound webhook {url} exhausted retries, moved to DLQ")


outbound_notifier = OutboundNotifier()


# ---------------------------------------------------------------------------
# Scheduled Pull Ingestion — periodically pull from external APIs
# ---------------------------------------------------------------------------
class PullIngestionConfig:
    """
    Manages configured external API sources to pull transactions from.
    Each source has: name, url, headers, interval_seconds, enabled.
    """

    def __init__(self):
        self._sources: list[dict] = []
        self._results: deque = deque(maxlen=200)
        self._lock = threading.Lock()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._load_from_env()

    def _load_from_env(self):
        """Load pull sources from PULL_INGESTION_SOURCES env var (JSON array)."""
        raw = os.getenv("PULL_INGESTION_SOURCES", "")
        if raw.strip():
            try:
                sources = json.loads(raw)
                if isinstance(sources, list):
                    self._sources = sources
                    logger.info(f"Pull ingestion configured: {len(sources)} source(s)")
            except json.JSONDecodeError:
                logger.warning("PULL_INGESTION_SOURCES is not valid JSON")

    def add_source(self, source: dict) -> dict:
        required = {"name", "url"}
        if not required.issubset(source.keys()):
            raise ValueError(f"Source must have: {required}")
        source.setdefault("interval_seconds", 300)
        source.setdefault("headers", {})
        source.setdefault("enabled", True)
        source["id"] = uuid.uuid4().hex[:8]
        with self._lock:
            self._sources.append(source)
        return source

    def remove_source(self, source_id: str) -> bool:
        with self._lock:
            before = len(self._sources)
            self._sources = [s for s in self._sources if s.get("id") != source_id]
            return len(self._sources) < before

    def list_sources(self) -> list[dict]:
        with self._lock:
            return [
                {k: v for k, v in s.items() if k != "headers"}
                for s in self._sources
            ]

    def get_results(self, limit: int = 50) -> list:
        return list(self._results)[-limit:]

    async def pull_once(self, source: dict) -> dict:
        """Pull transactions from a single source and score them."""
        url = source["url"]
        headers = source.get("headers", {})
        name = source.get("name", url)

        with tracer.start_as_current_span(f"pull_ingestion.{name}") as span:
            span.set_attribute("source.name", name)
            span.set_attribute("source.url", url)

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(url, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
            except Exception as e:
                result = {
                    "source": name,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "error",
                    "error": str(e),
                }
                self._results.append(result)
                span.record_exception(e)
                return result

            # Normalize: expect list of transactions or {"transactions": [...]}
            if isinstance(data, dict):
                txns = data.get("transactions") or data.get("data") or []
            elif isinstance(data, list):
                txns = data
            else:
                txns = []

            if not txns:
                result = {
                    "source": name,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "empty",
                    "ingested": 0,
                }
                self._results.append(result)
                return result

            # Score and store
            db = SessionLocal()
            try:
                scored = []
                flagged = 0
                for txn_data in txns[:10000]:
                    if not isinstance(txn_data, dict):
                        continue
                    r = score_and_store_transaction(txn_data, source=f"pull:{name}", db=db)
                    scored.append(r)
                    if r.get("decision") == "manual_review":
                        flagged += 1
                        await outbound_notifier.notify(r)
                    event_bus.publish(r)
            finally:
                db.close()

            result = {
                "source": name,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "ok",
                "ingested": len(scored),
                "flagged": flagged,
            }
            self._results.append(result)
            span.set_attribute("ingested", len(scored))
            span.set_attribute("flagged", flagged)
            return result

    async def run_loop(self):
        """Background loop that pulls from all enabled sources at their intervals."""
        self._running = True
        last_pull: dict[str, float] = {}

        while self._running:
            now = time.time()
            for source in self._sources:
                if not source.get("enabled", True):
                    continue
                sid = source.get("id", source["url"])
                interval = source.get("interval_seconds", 300)
                if now - last_pull.get(sid, 0) >= interval:
                    try:
                        await self.pull_once(source)
                    except Exception as e:
                        logger.error(f"Pull ingestion error for {source.get('name')}: {e}")
                    last_pull[sid] = now
            await asyncio.sleep(10)  # check every 10s

    def stop(self):
        self._running = False


pull_ingestion = PullIngestionConfig()


def _verify_webhook_key(
    x_webhook_key: Optional[str] = Header(None),
    key: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Verify webhook caller via API key. Key is from env or auto-generated (persisted, no dups)."""
    api_key = get_or_generate_key(db, "webhook_api_key", "WEBHOOK_API_KEY")
    provided = x_webhook_key or key
    if not provided:
        raise HTTPException(status_code=401, detail="Missing webhook API key. Provide X-Webhook-Key header or ?key= param.")
    if not hmac.compare_digest(provided, api_key):
        raise HTTPException(status_code=403, detail="Invalid webhook API key.")
    return True


def score_and_store_transaction(
    txn_data: Dict[str, Any],
    source: str,
    db: Session,
) -> Dict[str, Any]:
    """
    Shared pipeline: score a transaction and store the result.
    Used by both webhook ingestion and MCP ingestion.

    Args:
        txn_data: Dict with at least 'amount'. Optional: transaction_id, type/transaction_type, timestamp, currency, meta.
        source: Where this came from ('webhook', 'mcp', 'api').
        db: Database session.

    Returns:
        Dict with transaction_id, decision, anomaly_score, and stored status.
    """
    detector = get_detector()

    amount = float(txn_data.get("amount", 0))
    if amount <= 0:
        return {"error": "amount must be positive", "transaction_id": txn_data.get("transaction_id")}

    txn_id = txn_data.get("transaction_id") or f"{source}-{uuid.uuid4().hex[:12]}"
    txn_type = txn_data.get("type") or txn_data.get("transaction_type", "wire_transfer")
    ts_raw = txn_data.get("timestamp")
    currency = txn_data.get("currency", "USD")

    # Parse timestamp
    if ts_raw:
        try:
            ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            ts = datetime.utcnow()
    else:
        ts = datetime.utcnow()

    # Score
    with tracer.start_as_current_span(f"webhook.score.{source}") as span:
        span.set_attribute("transaction.id", txn_id)
        span.set_attribute("transaction.amount", amount)
        span.set_attribute("transaction.type", txn_type)
        span.set_attribute("transaction.source", source)

        score, details = detector.predict(amount=amount, timestamp=ts, txn_type=txn_type)
        risk_factors = details.get("risk_factors", [])

        if score > 0.7:
            decision = "manual_review"
        elif score > 0.4:
            decision = "approve"
        else:
            decision = "approve"

        span.set_attribute("transaction.anomaly_score", score)
        span.set_attribute("transaction.decision", decision)

    # Hash PII in meta before storage
    raw_meta = txn_data.get("meta") or {"source": source}
    meta, pii_risk = hash_pii_in_dict(raw_meta)

    # Store in DB
    existing = db.query(TransactionModel).filter(TransactionModel.transaction_id == txn_id).first()
    if existing:
        # Update existing
        existing.anomaly_score = score
        existing.is_anomaly = score > 0.5
        existing.anomaly_details = {
            "decision": decision,
            "risk_factors": risk_factors,
            "model_version": details.get("model_version"),
            "source": source,
            "features": details.get("features", {}),
            "pii_risk": pii_risk,
        }
        existing.status = "completed"
        existing.meta = meta
    else:
        # Create new
        txn = TransactionModel(
            transaction_id=txn_id,
            amount=amount,
            currency=currency,
            timestamp=ts,
            status="completed",
            is_anomaly=score > 0.5,
            anomaly_score=score,
            anomaly_details={
                "decision": decision,
                "risk_factors": risk_factors,
                "model_version": details.get("model_version"),
                "source": source,
                "features": details.get("features", {}),
                "pii_risk": pii_risk,
            },
            meta=meta,
        )
        db.add(txn)

    db.commit()

    try:
        from ..services.audit_trail_service import record_audit_event
        record_audit_event(
            db=db,
            event_type="transaction_scored",
            entity_type="transaction",
            entity_id=txn_id,
            actor_type="agent",
            summary=f"Transaction {txn_id} scored: {decision}",
            details={"decision": decision, "anomaly_score": score, "risk_factors": risk_factors},
            regulation_tags=["FINRA_4511", "SEC_17a4"],
        )
    except Exception:
        pass

    return {
        "transaction_id": txn_id,
        "decision": decision,
        "anomaly_score": round(score, 4),
        "risk_level": "high" if score > 0.7 else "medium" if score > 0.4 else "low",
        "risk_factors": risk_factors,
        "model_version": details.get("model_version", "unknown"),
        "stored": True,
        "source": source,
        "pii_risk": pii_risk,
    }


# ---------------------------------------------------------------------------
# POST /webhooks/transactions — single or batch ingestion
# ---------------------------------------------------------------------------
@router.post("/transactions")
async def ingest_transactions(
    request: Request,
    db: Session = Depends(get_db),
    _auth: bool = Depends(_verify_webhook_key),
):
    """
    Ingest one or more transactions from an external source.

    Accepts either a single transaction object or a list of transactions.
    Each transaction is scored by the ML compliance engine and stored.

    Required fields per transaction:
    - amount (float): Transaction amount

    Optional fields:
    - transaction_id (str): Unique ID (auto-generated if missing)
    - type / transaction_type (str): wire_transfer, ach, trade, internal, card, crypto
    - timestamp (str): ISO 8601 timestamp (defaults to now)
    - currency (str): Currency code (defaults to USD)
    - meta (dict): Any additional metadata

    Example single:
    ```json
    {"amount": 25000, "type": "wire_transfer", "transaction_id": "TXN-001"}
    ```

    Example batch (up to 10,000):
    ```json
    [
      {"amount": 25000, "type": "wire_transfer"},
      {"amount": 150, "type": "ach"},
      {"amount": 500000, "type": "trade", "timestamp": "2025-01-15T14:30:00"}
    ]
    ```
    """
    body = await request.json()

    # Normalize to list
    if isinstance(body, dict):
        transactions = [body]
    elif isinstance(body, list):
        transactions = body
    else:
        raise HTTPException(status_code=400, detail="Body must be a transaction object or list of transactions")

    if len(transactions) > 10000:
        raise HTTPException(status_code=400, detail=f"Maximum 10,000 transactions per request, got {len(transactions)}")

    results = []
    flagged = 0
    total_amount = 0.0

    for txn_data in transactions:
        if not isinstance(txn_data, dict):
            results.append({"error": "Each transaction must be an object"})
            continue
        result = score_and_store_transaction(txn_data, source="webhook", db=db)
        results.append(result)
        if result.get("decision") == "manual_review":
            flagged += 1
            await outbound_notifier.notify(result)
        total_amount += float(txn_data.get("amount", 0))
        event_bus.publish(result)

    return {
        "ingested": len(results),
        "flagged": flagged,
        "total_amount": round(total_amount, 2),
        "results": results,
    }


# ---------------------------------------------------------------------------
# GET /webhooks/results — retrieve scored results
# ---------------------------------------------------------------------------
@router.get("/results")
async def get_webhook_results(
    source: Optional[str] = None,
    flagged_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db),
    _auth: bool = Depends(_verify_webhook_key),
):
    """
    Retrieve previously scored transaction results.

    Args:
        source: Filter by source (webhook, mcp, api). Omit for all.
        flagged_only: If true, only return transactions with anomaly_score > 0.5
        limit: Max results (default 50, max 200)
    """
    limit = max(1, min(limit, 200))
    query = db.query(TransactionModel).filter(TransactionModel.anomaly_score.isnot(None))

    if flagged_only:
        query = query.filter(TransactionModel.is_anomaly == True)

    if source:
        # Filter by source in anomaly_details JSON
        # SQLite JSON support is limited, so we filter in Python
        pass

    transactions = query.order_by(TransactionModel.timestamp.desc()).limit(limit).all()

    results = []
    for t in transactions:
        details = t.anomaly_details or {}
        if source and details.get("source") != source:
            continue
        results.append({
            "transaction_id": t.transaction_id,
            "amount": t.amount,
            "currency": t.currency,
            "timestamp": t.timestamp.isoformat() if t.timestamp else None,
            "anomaly_score": t.anomaly_score,
            "is_anomaly": t.is_anomaly,
            "decision": details.get("decision"),
            "risk_factors": details.get("risk_factors", []),
            "source": details.get("source"),
            "model_version": details.get("model_version"),
        })

    return {
        "count": len(results),
        "results": results,
    }


# ---------------------------------------------------------------------------
# GET /webhooks/stream — SSE real-time compliance decision feed
# ---------------------------------------------------------------------------
@router.get("/stream")
async def stream_decisions(request: Request):
    """
    Server-Sent Events stream of compliance decisions in real-time.

    Every time a transaction is scored (via webhook, MCP, or pull ingestion),
    the result is broadcast here. Connect with EventSource in the browser
    or any SSE client.

    On connect, replays the last 50 events, then streams live.

    Example:
        const es = new EventSource('/webhooks/stream');
        es.onmessage = (e) => console.log(JSON.parse(e.data));
    """
    async def event_generator():
        q = event_bus.subscribe()
        try:
            # Replay recent events
            for event in event_bus.get_recent():
                yield f"data: {json.dumps(event, default=str)}\n\n"

            # Stream live
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield f"data: {json.dumps(event, default=str)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f": keepalive\n\n"
        finally:
            event_bus.unsubscribe(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/stream/status")
async def stream_status():
    """Get SSE stream status: subscriber count and recent event count."""
    return {
        "subscribers": event_bus.subscriber_count,
        "recent_events": len(event_bus.get_recent()),
    }


# ---------------------------------------------------------------------------
# Outbound webhook notification management
# ---------------------------------------------------------------------------
@router.post("/callbacks")
async def register_callback(
    request: Request,
    _auth: bool = Depends(_verify_webhook_key),
):
    """
    Register a callback URL for outbound webhook notifications.
    When a transaction is flagged (manual_review), the result is POSTed
    to all registered callback URLs with retry + dead letter queue.

    Body: {"url": "https://your-service.com/webhook"}
    """
    body = await request.json()
    url = body.get("url")
    if not url or not isinstance(url, str):
        raise HTTPException(status_code=400, detail="Body must have 'url' string field")
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
    outbound_notifier.register_callback(url)
    return {"registered": url, "total_callbacks": len(outbound_notifier.list_callbacks())}


@router.delete("/callbacks")
async def remove_callback(
    request: Request,
    _auth: bool = Depends(_verify_webhook_key),
):
    """Remove a callback URL. Body: {"url": "https://..."}"""
    body = await request.json()
    url = body.get("url")
    outbound_notifier.remove_callback(url)
    return {"removed": url, "total_callbacks": len(outbound_notifier.list_callbacks())}


@router.get("/callbacks")
async def list_callbacks(_auth: bool = Depends(_verify_webhook_key)):
    """List all registered outbound callback URLs."""
    return {
        "callbacks": outbound_notifier.list_callbacks(),
        "delivery_log": outbound_notifier.get_delivery_log(20),
    }


@router.get("/callbacks/dlq")
async def get_dead_letter_queue(
    limit: int = 50,
    _auth: bool = Depends(_verify_webhook_key),
):
    """
    Get the dead letter queue — failed outbound webhook deliveries
    that exhausted all retries.
    """
    items = outbound_notifier.get_dead_letter(limit)
    return {"count": len(items), "items": items}


# ---------------------------------------------------------------------------
# Scheduled pull ingestion management
# ---------------------------------------------------------------------------
@router.post("/pull/sources")
async def add_pull_source(
    request: Request,
    _auth: bool = Depends(_verify_webhook_key),
):
    """
    Add an external API source for scheduled pull ingestion.

    Body:
    {
        "name": "plaid-transactions",
        "url": "https://api.example.com/transactions",
        "headers": {"Authorization": "Bearer xxx"},
        "interval_seconds": 300,
        "enabled": true
    }

    The platform will GET that URL at the specified interval, expect a JSON
    list of transactions (or {"transactions": [...]}), and score each one.
    """
    body = await request.json()
    try:
        source = pull_ingestion.add_source(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"added": source}


@router.delete("/pull/sources/{source_id}")
async def remove_pull_source(
    source_id: str,
    _auth: bool = Depends(_verify_webhook_key),
):
    """Remove a pull ingestion source by ID."""
    removed = pull_ingestion.remove_source(source_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    return {"removed": source_id}


@router.get("/pull/sources")
async def list_pull_sources(_auth: bool = Depends(_verify_webhook_key)):
    """List all configured pull ingestion sources (headers redacted)."""
    return {
        "sources": pull_ingestion.list_sources(),
        "results": pull_ingestion.get_results(20),
    }


@router.post("/pull/trigger/{source_id}")
async def trigger_pull(
    source_id: str,
    _auth: bool = Depends(_verify_webhook_key),
):
    """Manually trigger a pull from a specific source (by ID)."""
    sources = pull_ingestion.list_sources()
    source = next((s for s in sources if s.get("id") == source_id), None)
    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    # Need full source with headers for the actual pull
    full_sources = pull_ingestion._sources
    full_source = next((s for s in full_sources if s.get("id") == source_id), None)
    if not full_source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    result = await pull_ingestion.pull_once(full_source)
    return result


@router.get("/status")
async def webhook_system_status():
    """
    Overview of the entire webhook/streaming system status.
    """
    return {
        "sse_stream": {
            "subscribers": event_bus.subscriber_count,
            "recent_events": len(event_bus.get_recent()),
        },
        "outbound_notifications": {
            "callbacks": len(outbound_notifier.list_callbacks()),
            "deliveries": len(outbound_notifier.get_delivery_log()),
            "dead_letter_queue": len(outbound_notifier.get_dead_letter()),
        },
        "pull_ingestion": {
            "sources": len(pull_ingestion.list_sources()),
            "recent_pulls": len(pull_ingestion.get_results()),
        },
    }
