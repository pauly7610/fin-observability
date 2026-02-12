"""
MCP Server for the Financial AI Observability Platform.

Exposes compliance monitoring, anomaly detection, explainability,
and metrics as MCP tools that any AI agent can connect to.

Connect via: https://fin-observability-production.up.railway.app/mcp
"""
from mcp.server.fastmcp import FastMCP
from datetime import datetime
from typing import Optional, List
from opentelemetry import trace, metrics
import time
import json
import logging
import threading
import hashlib

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("mcp.server")
meter = metrics.get_meter("mcp.server")

# ---------------------------------------------------------------------------
# MCP Usage Tracking (in-memory, exposed via /mcp/stats)
# ---------------------------------------------------------------------------
_usage_lock = threading.Lock()
_usage_log: List[dict] = []
_MAX_USAGE_LOG = 10000

def _record_usage(tool_name: str, latency_ms: float, decision: str = "", error: str = ""):
    """Record a tool invocation for usage tracking."""
    entry = {
        "tool": tool_name,
        "timestamp": datetime.utcnow().isoformat(),
        "latency_ms": round(latency_ms, 1),
        "decision": decision,
        "error": error,
    }
    with _usage_lock:
        _usage_log.append(entry)
        if len(_usage_log) > _MAX_USAGE_LOG:
            _usage_log.pop(0)

def get_usage_stats() -> dict:
    """Get aggregated MCP usage statistics."""
    with _usage_lock:
        log = list(_usage_log)
    if not log:
        return {"total_calls": 0, "tools": {}, "avg_latency_ms": 0, "errors": 0, "recent": []}

    tool_counts = {}
    total_latency = 0.0
    errors = 0
    for entry in log:
        tool_counts[entry["tool"]] = tool_counts.get(entry["tool"], 0) + 1
        total_latency += entry["latency_ms"]
        if entry["error"]:
            errors += 1

    return {
        "total_calls": len(log),
        "tools": tool_counts,
        "avg_latency_ms": round(total_latency / len(log), 1),
        "errors": errors,
        "recent": log[-10:][::-1],
    }

# ---------------------------------------------------------------------------
# OTel Metrics
# ---------------------------------------------------------------------------
mcp_tool_calls = meter.create_counter(
    name="mcp_tool_calls_total",
    description="Total MCP tool invocations",
)
mcp_tool_duration = meter.create_histogram(
    name="mcp_tool_duration_ms",
    description="MCP tool call duration in milliseconds",
    unit="ms",
)

# ---------------------------------------------------------------------------
# Rate Limiter (per-tool, sliding window)
# ---------------------------------------------------------------------------
_rate_lock = threading.Lock()
_rate_buckets: dict = {}
RATE_LIMIT = 60  # calls per minute

def _check_rate_limit(tool_name: str) -> bool:
    """Returns True if within rate limit, False if exceeded."""
    now = time.time()
    key = tool_name
    with _rate_lock:
        if key not in _rate_buckets:
            _rate_buckets[key] = []
        # Prune old entries
        _rate_buckets[key] = [t for t in _rate_buckets[key] if now - t < 60]
        if len(_rate_buckets[key]) >= RATE_LIMIT:
            return False
        _rate_buckets[key].append(now)
        return True

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
VALID_TXN_TYPES = {"wire_transfer", "wire", "ach", "trade", "internal", "card", "crypto"}

def _validate_amount(amount: float) -> float:
    if amount <= 0:
        raise ValueError(f"Amount must be positive, got {amount}")
    if amount > 1_000_000_000:
        raise ValueError(f"Amount exceeds maximum (1B), got {amount}")
    return amount

def _validate_txn_type(txn_type: str) -> str:
    t = txn_type.lower().strip()
    if t not in VALID_TXN_TYPES:
        raise ValueError(f"Unknown transaction_type '{txn_type}'. Valid: {', '.join(sorted(VALID_TXN_TYPES))}")
    return t

def _parse_timestamp(ts: Optional[str]) -> str:
    if ts is None:
        return datetime.utcnow().isoformat()
    try:
        datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return ts
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid timestamp format: '{ts}'. Use ISO 8601 (e.g. 2025-01-15T14:30:00)")

def _score_to_decision(score: float) -> tuple:
    """Map anomaly score to (decision, confidence, reasoning)."""
    if score > 0.7:
        return "manual_review", 85.0, f"High anomaly score ({score:.3f}) requires human review."
    elif score > 0.4:
        return "approve", 75.0, f"Approved with elevated monitoring. Anomaly score: {score:.3f}."
    else:
        return "approve", 90.0, f"Transaction passed all compliance checks. Anomaly score: {score:.3f}."

# ---------------------------------------------------------------------------
# Traced tool wrapper
# ---------------------------------------------------------------------------
def _traced_tool(tool_name: str, func, **kwargs):
    """Execute a tool function with OTel tracing, metrics, rate limiting, and usage tracking."""
    if not _check_rate_limit(tool_name):
        mcp_tool_calls.add(1, {"tool": tool_name, "status": "rate_limited"})
        _record_usage(tool_name, 0, error="rate_limited")
        return {"error": f"Rate limit exceeded ({RATE_LIMIT}/min). Please slow down."}

    start = time.perf_counter()
    with tracer.start_as_current_span(f"mcp.tool.{tool_name}") as span:
        span.set_attribute("mcp.tool.name", tool_name)
        for k, v in kwargs.items():
            if v is not None and not isinstance(v, (list, dict)):
                span.set_attribute(f"mcp.tool.param.{k}", str(v))
        try:
            result = func(**kwargs)
            latency = (time.perf_counter() - start) * 1000
            decision = result.get("decision", "") if isinstance(result, dict) else ""
            span.set_attribute("mcp.tool.decision", decision)
            span.set_attribute("mcp.tool.latency_ms", latency)
            mcp_tool_calls.add(1, {"tool": tool_name, "status": "ok", "decision": decision})
            mcp_tool_duration.record(latency, {"tool": tool_name})
            _record_usage(tool_name, latency, decision=decision)
            return result
        except ValueError as e:
            latency = (time.perf_counter() - start) * 1000
            span.set_attribute("mcp.tool.error", str(e))
            mcp_tool_calls.add(1, {"tool": tool_name, "status": "validation_error"})
            _record_usage(tool_name, latency, error=str(e))
            return {"error": str(e)}
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            span.set_attribute("mcp.tool.error", str(e))
            mcp_tool_calls.add(1, {"tool": tool_name, "status": "error"})
            _record_usage(tool_name, latency, error=str(e))
            logger.exception(f"MCP tool {tool_name} failed")
            return {"error": f"Internal error: {type(e).__name__}: {e}"}

# ---------------------------------------------------------------------------
# Core logic (pure functions, no MCP decorators)
# ---------------------------------------------------------------------------
def _check_compliance_single(amount: float, transaction_type: str, timestamp: str, transaction_id: str) -> dict:
    from apps.backend.ml.anomaly_detector import get_detector

    amount = _validate_amount(amount)
    txn_type = _validate_txn_type(transaction_type)
    ts = _parse_timestamp(timestamp)

    detector = get_detector()
    score, details = detector.predict(amount=amount, timestamp=ts, txn_type=txn_type)
    risk_factors = details.get("risk_factors", [])
    decision, confidence, reasoning = _score_to_decision(score)

    if risk_factors:
        reasoning += f" Risk factors: {'; '.join(risk_factors)}."

    return {
        "transaction_id": transaction_id,
        "decision": decision,
        "confidence": confidence,
        "reasoning": reasoning,
        "anomaly_score": round(score, 4),
        "risk_level": "high" if score > 0.7 else "medium" if score > 0.4 else "low",
        "risk_factors": risk_factors,
        "model_version": details.get("model_version", "unknown"),
        "features": details.get("features", {}),
        "regulation": "FINRA_4511",
    }

def _explain_single(amount: float, transaction_type: str, timestamp: str) -> dict:
    from apps.backend.ml.anomaly_detector import get_detector

    amount = _validate_amount(amount)
    txn_type = _validate_txn_type(transaction_type)
    ts = _parse_timestamp(timestamp)

    detector = get_detector()
    score, details = detector.predict(amount=amount, timestamp=ts, txn_type=txn_type)
    decision, confidence, reasoning = _score_to_decision(score)

    try:
        shap_result = detector.explain(amount=amount, timestamp=ts, txn_type=txn_type)
    except Exception as e:
        shap_result = {"error": str(e), "shap_values": []}

    return {
        "anomaly_score": round(score, 4),
        "decision": decision,
        "confidence": confidence,
        "reasoning": reasoning,
        "explanation": shap_result,
        "feature_details": details,
    }

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "Financial AI Observability",
    instructions=(
        "You are connected to a financial compliance and observability platform. "
        "Use the available tools to check transaction compliance, explain ML decisions, "
        "analyze portfolios, and monitor system health. All tools are read-only safe.\n\n"
        "Key tools:\n"
        "- check_transaction_compliance: Score a single transaction\n"
        "- explain_transaction: Get SHAP feature importance for a decision\n"
        "- batch_check_compliance: Score multiple transactions at once\n"
        "- analyze_portfolio: Aggregate risk assessment across a set of transactions\n"
        "- get_compliance_metrics: Real-time approval/block/review rates\n"
        "- get_drift_status: Model drift detection (PSI + KS tests)\n"
    ),
)


@mcp.tool()
def check_transaction_compliance(
    amount: float,
    transaction_type: str = "wire_transfer",
    timestamp: Optional[str] = None,
    transaction_id: Optional[str] = None,
) -> dict:
    """
    Run a transaction through the ML-powered compliance engine.

    Returns an approve/block/manual_review decision with confidence score,
    anomaly score, risk factors, and regulatory reference (FINRA 4511, SEC 17a-4).

    Args:
        amount: Transaction amount in USD (must be > 0, max 1B)
        transaction_type: One of: wire_transfer, wire, ach, trade, internal, card, crypto
        timestamp: ISO 8601 timestamp (defaults to now)
        transaction_id: Optional ID for tracking
    """
    txn_id = transaction_id or f"mcp-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    return _traced_tool(
        "check_transaction_compliance",
        _check_compliance_single,
        amount=amount,
        transaction_type=transaction_type,
        timestamp=timestamp,
        transaction_id=txn_id,
    )


@mcp.tool()
def explain_transaction(
    amount: float,
    transaction_type: str = "wire_transfer",
    timestamp: Optional[str] = None,
) -> dict:
    """
    Get SHAP-based explainability for a compliance decision.

    Returns per-feature SHAP importance values showing WHY the ML model
    flagged or approved a transaction. Uses TreeExplainer on Isolation Forest.

    Args:
        amount: Transaction amount in USD (must be > 0, max 1B)
        transaction_type: One of: wire_transfer, wire, ach, trade, internal, card, crypto
        timestamp: ISO 8601 timestamp (defaults to now)
    """
    return _traced_tool(
        "explain_transaction",
        _explain_single,
        amount=amount,
        transaction_type=transaction_type,
        timestamp=timestamp,
    )


@mcp.tool()
def batch_check_compliance(
    transactions: List[dict],
) -> dict:
    """
    Check multiple transactions in one call. Ideal for scanning a ledger or batch.

    Each transaction should have: amount (required), transaction_type, timestamp, transaction_id.
    Returns results for each transaction plus aggregate statistics.

    Args:
        transactions: List of transaction dicts, each with at least 'amount' key.
                      Example: [{"amount": 5000, "transaction_type": "wire"}, {"amount": 150}]
    """
    def _batch_impl(transactions):
        if not transactions:
            raise ValueError("transactions list is empty")
        if len(transactions) > 10000:
            raise ValueError(f"Maximum 10,000 transactions per batch, got {len(transactions)}")

        results = []
        flagged = 0
        total_amount = 0.0

        for i, txn in enumerate(transactions):
            if not isinstance(txn, dict):
                results.append({"index": i, "error": "Each transaction must be a dict"})
                continue
            amt = txn.get("amount")
            if amt is None:
                results.append({"index": i, "error": "Missing required field: amount"})
                continue

            txn_id = txn.get("transaction_id", f"batch-{i}")
            result = _check_compliance_single(
                amount=float(amt),
                transaction_type=txn.get("transaction_type", "wire_transfer"),
                timestamp=txn.get("timestamp"),
                transaction_id=txn_id,
            )
            result["index"] = i
            results.append(result)
            total_amount += float(amt)
            if result.get("decision") == "manual_review":
                flagged += 1

        return {
            "total": len(transactions),
            "processed": len([r for r in results if "error" not in r or "decision" in r]),
            "flagged": flagged,
            "total_amount": round(total_amount, 2),
            "results": results,
        }

    return _traced_tool("batch_check_compliance", _batch_impl, transactions=transactions)


@mcp.tool()
def analyze_portfolio(
    transactions: List[dict],
) -> dict:
    """
    Aggregate risk assessment across a portfolio of transactions.

    Instead of per-transaction results, returns a portfolio-level summary:
    risk distribution, top flagged items, concentration analysis, and
    an overall portfolio risk score.

    Args:
        transactions: List of transaction dicts, each with at least 'amount' key.
                      Example: [{"amount": 5000, "transaction_type": "wire"}, ...]
    """
    def _portfolio_impl(transactions):
        if not transactions:
            raise ValueError("transactions list is empty")
        if len(transactions) > 10000:
            raise ValueError(f"Maximum 10,000 transactions per portfolio, got {len(transactions)}")

        from apps.backend.ml.anomaly_detector import get_detector
        detector = get_detector()

        scores = []
        flagged_items = []
        type_amounts = {}
        total_amount = 0.0

        for i, txn in enumerate(transactions):
            if not isinstance(txn, dict) or "amount" not in txn:
                continue
            amt = float(txn["amount"])
            txn_type = txn.get("transaction_type", "wire_transfer")
            ts = txn.get("timestamp") or datetime.utcnow().isoformat()

            try:
                _validate_amount(amt)
                t = _validate_txn_type(txn_type)
                ts = _parse_timestamp(ts)
            except ValueError:
                continue

            score, details = detector.predict(amount=amt, timestamp=ts, txn_type=t)
            scores.append(score)
            total_amount += amt

            # Track by type
            type_amounts[txn_type] = type_amounts.get(txn_type, 0.0) + amt

            if score > 0.5:
                flagged_items.append({
                    "index": i,
                    "transaction_id": txn.get("transaction_id", f"portfolio-{i}"),
                    "amount": amt,
                    "type": txn_type,
                    "anomaly_score": round(score, 4),
                    "risk_factors": details.get("risk_factors", []),
                })

        if not scores:
            raise ValueError("No valid transactions to analyze")

        # Sort flagged by score descending
        flagged_items.sort(key=lambda x: x["anomaly_score"], reverse=True)

        avg_score = sum(scores) / len(scores)
        high_risk = sum(1 for s in scores if s > 0.7)
        medium_risk = sum(1 for s in scores if 0.4 < s <= 0.7)
        low_risk = sum(1 for s in scores if s <= 0.4)

        # Portfolio risk score: weighted by amount
        portfolio_risk = "low"
        if avg_score > 0.5 or high_risk > len(scores) * 0.1:
            portfolio_risk = "high"
        elif avg_score > 0.3 or high_risk > 0:
            portfolio_risk = "medium"

        # Concentration: any single type > 60% of total
        concentration_warnings = []
        for t, amt in type_amounts.items():
            pct = (amt / total_amount * 100) if total_amount > 0 else 0
            if pct > 60:
                concentration_warnings.append(f"{t} represents {pct:.0f}% of portfolio value")

        return {
            "portfolio_risk": portfolio_risk,
            "avg_anomaly_score": round(avg_score, 4),
            "total_transactions": len(scores),
            "total_amount": round(total_amount, 2),
            "risk_distribution": {
                "high": high_risk,
                "medium": medium_risk,
                "low": low_risk,
            },
            "flagged_count": len(flagged_items),
            "top_flagged": flagged_items[:10],
            "type_breakdown": {t: round(a, 2) for t, a in type_amounts.items()},
            "concentration_warnings": concentration_warnings,
        }

    return _traced_tool("analyze_portfolio", _portfolio_impl, transactions=transactions)


@mcp.tool()
def get_compliance_metrics() -> dict:
    """
    Get real-time compliance monitoring metrics.

    Returns total transactions processed, approval/block/review rates,
    average confidence score, and current model information.
    """
    def _impl():
        from apps.backend.services.metrics_service import get_metrics_service
        from apps.backend.ml.anomaly_detector import get_detector

        metrics_svc = get_metrics_service()
        m = metrics_svc.get_metrics()
        m["model"] = get_detector().get_model_info()
        return m

    return _traced_tool("get_compliance_metrics", _impl)


@mcp.tool()
def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 20,
) -> dict:
    """
    List recent compliance incidents from the platform.

    Args:
        status: Filter by status (open, resolved, escalated). Omit for all.
        severity: Filter by severity (critical, high, medium, low). Omit for all.
        limit: Max incidents to return (default 20, max 50)
    """
    def _impl(status, severity, limit):
        from apps.backend.database import SessionLocal
        from apps.backend.models import Incident as IncidentModel

        limit = max(1, min(limit, 50))
        db = SessionLocal()
        try:
            query = db.query(IncidentModel)
            if status:
                query = query.filter(IncidentModel.status == status)
            if severity:
                query = query.filter(IncidentModel.severity == severity)
            incidents = query.order_by(IncidentModel.created_at.desc()).limit(limit).all()
            return {
                "count": len(incidents),
                "incidents": [
                    {
                        "id": i.incident_id,
                        "title": i.title,
                        "description": i.description,
                        "status": i.status,
                        "severity": i.severity,
                        "type": i.type,
                        "created_at": i.created_at.isoformat() if i.created_at else None,
                    }
                    for i in incidents
                ],
            }
        finally:
            db.close()

    return _traced_tool("list_incidents", _impl, status=status, severity=severity, limit=limit)


@mcp.tool()
def get_drift_status() -> dict:
    """
    Get current model drift detection status.

    Returns PSI (Population Stability Index) and KS test results per feature,
    drift thresholds, and whether retraining is recommended.
    """
    def _impl():
        from apps.backend.ml.drift_detector import get_drift_detector
        return get_drift_detector().get_status()

    return _traced_tool("get_drift_status", _impl)


@mcp.tool()
def get_model_leaderboard() -> dict:
    """
    Get the evaluation leaderboard of model versions ranked by F1 score.

    Shows precision, recall, F1, and sample count for each evaluated model version.
    """
    def _impl():
        from apps.backend.services.evalai_service import get_evalai_service
        return get_evalai_service().get_leaderboard()

    return _traced_tool("get_model_leaderboard", _impl)


# ---------------------------------------------------------------------------
# Tool: Ingest Transactions (MCP data ingestion)
# ---------------------------------------------------------------------------
@mcp.tool()
def ingest_transactions(
    transactions: List[dict],
) -> dict:
    """
    Ingest and score transactions from your system. Each transaction is run
    through the ML compliance engine, stored in the database, and available
    for future queries via list_incidents and get_compliance_metrics.

    This is the MCP equivalent of the webhook endpoint — use it to push
    your own transaction data for continuous compliance monitoring.

    Each transaction needs at least 'amount'. Optional: transaction_id,
    type/transaction_type, timestamp, currency, meta.

    Args:
        transactions: List of transaction dicts.
                      Example: [{"amount": 5000, "type": "wire"}, {"amount": 150, "type": "ach"}]
    """
    def _impl(transactions):
        if not transactions:
            raise ValueError("transactions list is empty")
        if len(transactions) > 10000:
            raise ValueError(f"Maximum 10,000 transactions per ingestion, got {len(transactions)}")

        from apps.backend.database import SessionLocal
        from apps.backend.routers.webhooks import score_and_store_transaction

        db = SessionLocal()
        try:
            results = []
            flagged = 0
            total_amount = 0.0

            for txn_data in transactions:
                if not isinstance(txn_data, dict):
                    results.append({"error": "Each transaction must be a dict"})
                    continue
                amt = txn_data.get("amount")
                if amt is None:
                    results.append({"error": "Missing required field: amount"})
                    continue

                result = score_and_store_transaction(txn_data, source="mcp", db=db)
                results.append(result)
                if result.get("decision") == "manual_review":
                    flagged += 1
                total_amount += float(amt)

            return {
                "ingested": len([r for r in results if "stored" in r]),
                "flagged": flagged,
                "total_amount": round(total_amount, 2),
                "results": results,
            }
        finally:
            db.close()

    return _traced_tool("ingest_transactions", _impl, transactions=transactions)


# ---------------------------------------------------------------------------
# Resources (live data, not static strings)
# ---------------------------------------------------------------------------
@mcp.resource("platform://metrics")
def resource_metrics() -> str:
    """Current compliance metrics as JSON."""
    from apps.backend.services.metrics_service import get_metrics_service
    return json.dumps(get_metrics_service().get_metrics(), default=str)


@mcp.resource("platform://drift")
def resource_drift() -> str:
    """Current model drift status as JSON."""
    from apps.backend.ml.drift_detector import get_drift_detector
    return json.dumps(get_drift_detector().get_status(), default=str)


@mcp.resource("platform://regulations")
def resource_regulations() -> str:
    """Supported regulatory frameworks with thresholds."""
    return json.dumps({
        "FINRA_4511": {
            "name": "FINRA Rule 4511 - Books and Records",
            "description": "Requires firms to make and preserve books and records",
            "thresholds": {"anomaly_review": 0.7, "elevated_monitoring": 0.4},
        },
        "SEC_17a4": {
            "name": "SEC Rule 17a-4 - Record Retention",
            "description": "Requires broker-dealers to preserve certain records",
            "retention_years": 6,
        },
        "Basel_III_LCR": {
            "name": "Basel III Liquidity Coverage Ratio",
            "description": "Banks must hold enough liquid assets to cover 30-day outflows",
            "minimum_lcr_pct": 100,
        },
    })
