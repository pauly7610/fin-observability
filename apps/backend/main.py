from fastapi import Body, Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from opentelemetry import trace

from apps.backend.broadcast import incident_broadcaster
from apps.backend.database import engine, SessionLocal, get_db
from apps.backend.models import Base
from apps.backend.rate_limit import limiter
from apps.backend.routers import approval
from apps.backend.telemetry import (
    init_telemetry,
    metrics_middleware,
    export_job_counter,
    compliance_action_counter,
    anomaly_detected_counter,
    http_request_counter,
    http_request_duration,
)
import logging
import os
import structlog
from datetime import datetime, timedelta


def get_logger(name=None):
    logger = structlog.get_logger(name)
    span = trace.get_current_span()
    ctx = span.get_span_context() if span else None
    trace_id = format(ctx.trace_id, "x") if ctx and hasattr(ctx, "trace_id") else None
    span_id = format(ctx.span_id, "x") if ctx and hasattr(ctx, "span_id") else None
    return logger.bind(trace_id=trace_id, span_id=span_id)


# Configure structlog for JSON output and stdlib compatibility
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
logging.basicConfig(level=logging.INFO, format="%(message)s")

# Instrument database and HTTP clients for tracing
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

SQLAlchemyInstrumentor().instrument(engine=engine)
RequestsInstrumentor().instrument()
try:
    from opentelemetry.instrumentation.boto3s3 import Boto3S3Instrumentor
    Boto3S3Instrumentor().instrument()
except ImportError:
    pass

from apps.backend.routers import (
    admin,
    agent,
    auth,
    ops,
    ops_trigger,
    audit,
    compliance,
    incidents,
    transactions,
    system_metrics,
    users,
    verification,
    anomaly,
    export_metadata,
    ops_metrics,
    webhooks,
)
from apps.backend.scheduled_exports import schedule_exports
from apps.backend.security import get_current_user
from apps.backend.agentic_escalation import escalate_overdue_agent_actions
from apscheduler.schedulers.background import BackgroundScheduler

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize OpenTelemetry (tracing + metrics)
init_telemetry()
tracer = trace.get_tracer(__name__)

app = FastAPI(
    title="Financial AI Observability Platform",
    description="Backend API for financial services observability and automation",
    version="0.1.0",
)
app.include_router(approval.router)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS - supports multiple origins via CORS_ORIGINS env var
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin.router)
app.include_router(anomaly.router)
app.include_router(compliance.router)
app.include_router(agent.router)
app.include_router(ops.router)
app.include_router(ops_trigger.router)
app.include_router(audit.router)
app.include_router(incidents.router)
app.include_router(transactions.router)
app.include_router(system_metrics.router)
app.include_router(users.router)
app.include_router(verification.router)
app.include_router(auth.router)
app.include_router(ops_metrics.router)
app.include_router(export_metadata.router)
app.include_router(webhooks.router)

# MCP server: register /mcp/stats and /mcp/tools BEFORE mount so they take precedence
try:
    from apps.backend.mcp_server import mcp as mcp_instance, get_usage_stats

    @app.get("/mcp/stats", tags=["mcp"])
    async def mcp_stats(user=Depends(get_current_user)):
        """Get MCP tool usage statistics."""
        return get_usage_stats()

    @app.get("/mcp/tools", tags=["mcp"])
    async def mcp_tools(request: Request, user=Depends(get_current_user)):
        """Get list of available MCP tools with descriptions."""
        tools = mcp_instance._tool_manager.list_tools()
        env_url = os.getenv("MCP_PUBLIC_URL") or os.getenv("API_URL")
        mcp_url = (env_url.rstrip("/") + "/mcp") if env_url else str(request.base_url).rstrip("/") + "/mcp"
        return {
            "endpoint": mcp_url,
            "transport": "streamable-http",
            "tool_count": len(tools),
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.inputSchema if hasattr(t, 'inputSchema') else {},
                }
                for t in tools
            ],
        }

    mcp_app = mcp_instance.streamable_http_app()
    app.mount("/mcp", mcp_app)
    logging.getLogger(__name__).info("MCP server mounted at /mcp")
except Exception as e:
    logging.getLogger(__name__).warning(f"MCP server failed to mount: {e}")

# Instrument FastAPI with OpenTelemetry
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)

# Custom metrics middleware
app.middleware("http")(metrics_middleware)

# MCP API key auth: when MCP_API_KEY is set in env or auto-generated, require it for MCP protocol requests
MCP_DASHBOARD_PATHS = {"/mcp/stats", "/mcp/tools"}


def _get_mcp_api_key():
    """Resolve MCP key from env or auto-generated (persisted, no dups). Cached per process."""
    from apps.backend.database import SessionLocal
    from apps.backend.key_utils import get_or_generate_key
    if not hasattr(_get_mcp_api_key, "_cache"):
        _get_mcp_api_key._cache = None
    from_env = os.getenv("MCP_API_KEY", "").strip()
    if from_env:
        return from_env
    if _get_mcp_api_key._cache is not None:
        return _get_mcp_api_key._cache
    db = SessionLocal()
    try:
        key = get_or_generate_key(db, "mcp_api_key", "MCP_API_KEY")
        _get_mcp_api_key._cache = key
        return key
    finally:
        db.close()


@app.middleware("http")
async def mcp_api_key_auth(request: Request, call_next):
    path = request.url.path.rstrip("/")
    if not path.startswith("/mcp") or path in MCP_DASHBOARD_PATHS:
        return await call_next(request)
    mcp_key = _get_mcp_api_key()
    provided = (
        request.headers.get("x-mcp-api-key")
        or (request.headers.get("authorization") or "").replace("Bearer ", "").strip()
    )
    if provided != mcp_key:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=401, content={"detail": "Invalid or missing MCP API key"})
    return await call_next(request)

# Start scheduled exports
schedule_exports()

# Start agentic escalation job
scheduler = BackgroundScheduler()


def escalation_job():
    db = SessionLocal()
    try:
        count = escalate_overdue_agent_actions(db)
        if count > 0:
            print(f"[Agentic Escalation] Auto-escalated {count} overdue agent actions.")
    finally:
        db.close()


scheduler.add_job(escalation_job, "interval", hours=1, id="agentic_escalation")

# Start automated retraining pipeline (drift-triggered)
from apps.backend.ml.retraining_pipeline import get_retraining_pipeline, RETRAIN_INTERVAL_HOURS

DRIFT_CHECK_HOURS = int(os.environ.get("DRIFT_CHECK_HOURS", "6"))

def retraining_job():
    pipeline = get_retraining_pipeline()
    result = pipeline.run_if_drifted()
    logging.info(f"[Retraining Pipeline] {result.get('status')}: trigger={result.get('trigger', 'drift_check')}")

scheduler.add_job(retraining_job, "interval", hours=DRIFT_CHECK_HOURS, id="drift_check_retraining")
scheduler.start()

# Start pull ingestion background loop if sources are configured
from apps.backend.routers.webhooks import pull_ingestion

@app.on_event("startup")
async def start_pull_ingestion():
    if pull_ingestion._sources:
        import asyncio
        pull_ingestion._task = asyncio.create_task(pull_ingestion.run_loop())
        logging.getLogger(__name__).info(f"Pull ingestion started with {len(pull_ingestion._sources)} source(s)")

@app.on_event("shutdown")
async def stop_pull_ingestion():
    pull_ingestion.stop()

# Start Kafka consumer in-app when KAFKA_BROKERS is set
import threading

@app.on_event("startup")
async def start_kafka_consumer():
    brokers = os.getenv("KAFKA_BROKERS", "")
    if not brokers:
        return
    try:
        from apps.backend.kafka_consumer_service import run_consumer, set_main_loop
        import asyncio
        set_main_loop(asyncio.get_running_loop())
        t = threading.Thread(target=run_consumer, daemon=True)
        t.start()
        logging.getLogger(__name__).info(f"Kafka consumer started (brokers={brokers})")
    except Exception as e:
        logging.getLogger(__name__).warning(f"Kafka consumer failed to start: {e}")

# Limiter is now created below and imported by routers


@app.get("/")
async def root():
    return {
        "name": "Financial AI Observability Platform",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "compliance_monitor": "/agent/compliance/monitor",
            "compliance_status": "/agent/compliance/status",
            "compliance_metrics": "/agent/compliance/metrics",
            "explainability": "/agent/compliance/explain",
            "ensemble": "/agent/compliance/ensemble",
            "experiments": "/agent/compliance/experiments",
            "evaluation": "/agent/compliance/eval/results",
            "leaderboard": "/agent/compliance/eval/leaderboard",
        },
    }


@app.get("/health")
@limiter.limit("5/minute")  # Example: 5 requests per minute per IP
async def health_check(request: Request):
    return {"status": "healthy"}


async def _validate_websocket_token(websocket: WebSocket) -> bool:
    """Validate token from query param (?token=...). Returns True if valid, else closes with 4001."""
    ws_auth_disabled = os.getenv("WS_AUTH_DISABLED", "false").lower() == "true"
    if ws_auth_disabled:
        return True
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return False
    from apps.backend.routers.auth import decode_access_token
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        await websocket.close(code=4001)
        return False
    return True


@app.websocket("/ws/incidents")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time incident updates.
    Clients receive JSON strings with new/updated incidents.
    Auth: pass ?token=<jwt> or set WS_AUTH_DISABLED=true for dev.
    """
    await websocket.accept()
    if not await _validate_websocket_token(websocket):
        return
    await incident_broadcaster.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keepalive
    except WebSocketDisconnect:
        incident_broadcaster.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket /ws/incidents error: {e}")
        await websocket.close()


@app.websocket("/ws/compliance")
async def compliance_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time compliance updates.
    Auth: pass ?token=<jwt> or set WS_AUTH_DISABLED=true for dev.
    """
    await websocket.accept()
    if not await _validate_websocket_token(websocket):
        return
    try:
        while True:
            await websocket.receive_text()  # keepalive
    except WebSocketDisconnect:
        pass


@app.post("/api/compliance/check")
async def api_compliance_check(
    body: dict = Body(...),
    user=Depends(get_current_user),
):
    """MCP-equivalent compliance check. Returns same shape as check_transaction_compliance tool."""
    from apps.backend.mcp_server import _check_compliance_single
    from datetime import datetime as dt

    amount = body.get("amount")
    if amount is None:
        raise HTTPException(status_code=400, detail="Missing required field: amount")
    transaction_type = body.get("transaction_type", "wire_transfer")
    timestamp = body.get("timestamp") or dt.utcnow().isoformat()
    transaction_id = body.get("transaction_id") or f"api-{dt.utcnow().strftime('%Y%m%d%H%M%S%f')}"

    try:
        return _check_compliance_single(
            amount=float(amount),
            transaction_type=str(transaction_type),
            timestamp=timestamp,
            transaction_id=str(transaction_id),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/metrics")
async def get_platform_metrics(user=Depends(get_current_user)):
    """Return platform-level metrics for the frontend dashboard."""
    from apps.backend.database import SessionLocal
    from apps.backend.models import Incident, ComplianceLog
    now = datetime.utcnow()
    db = SessionLocal()
    try:
        # Active alerts count
        active_alerts = db.query(Incident).filter(
            Incident.status.in_(["open", "investigating"])
        ).count()
        # Compliance stats
        total_compliance = db.query(ComplianceLog).count()
        resolved_compliance = db.query(ComplianceLog).filter(
            ComplianceLog.is_resolved == True
        ).count()
        compliance_score = round(
            (resolved_compliance / total_compliance * 100) if total_compliance > 0 else 100, 1
        )
        # Uptime approximation (based on resolved vs total incidents)
        total_incidents = db.query(Incident).count()
        resolved_incidents = db.query(Incident).filter(
            Incident.status.in_(["resolved", "closed"])
        ).count()
        uptime = round(
            99.9 - (max(0, total_incidents - resolved_incidents) * 0.1), 1
        )
        return {
            "uptime": min(uptime, 99.99),
            "activeAlerts": active_alerts,
            "noiseReduction": 94,
            "mttr": 12,
            "mttrImprovement": 35,
            "complianceScore": compliance_score,
            "complianceStatus": "Compliant" if compliance_score >= 80 else "At Risk",
        }
    finally:
        db.close()


@app.get("/api/kafka/status")
async def get_kafka_status(user=Depends(get_current_user)):
    """Return Kafka consumer status for the Connect page."""
    brokers = os.getenv("KAFKA_BROKERS", "")
    topics = os.getenv("KAFKA_TOPICS", "orders,executions,trades").split(",")
    threshold = os.getenv("STUCK_ORDER_THRESHOLD_MINUTES", "5")
    return {
        "enabled": bool(brokers),
        "brokers": brokers or "(not configured)",
        "topics": topics,
        "stuck_order_threshold_minutes": int(threshold),
    }


@app.get("/api/systems")
async def get_systems(user=Depends(get_current_user), db=Depends(get_db)):
    from apps.backend.models import SystemMetric

    systems_config = os.getenv("SYSTEMS_CONFIG", "")
    if systems_config:
        try:
            import json
            configs = json.loads(systems_config)
            now = datetime.utcnow().isoformat()
            return {
                "systems": [
                    {"id": c.get("id", i), "name": c.get("name", "System"), "status": "operational", "last_updated": now}
                    for i, c in enumerate(configs, 1)
                ]
            }
        except (json.JSONDecodeError, TypeError):
            pass

    from sqlalchemy import distinct, func
    rows = db.query(distinct(SystemMetric.metric_name)).filter(SystemMetric.metric_name.isnot(None)).all()
    if not rows:
        return {"systems": []}
    names = [r[0] for r in rows if r[0]]
    if not names:
        return {"systems": []}
    systems = []
    for i, name in enumerate(names[:50], 1):
        latest = db.query(SystemMetric).filter(SystemMetric.metric_name == name).order_by(SystemMetric.timestamp.desc()).first()
        status = "degraded" if (latest and latest.is_anomaly) else "operational"
        last_updated = latest.timestamp.isoformat() if latest and latest.timestamp else datetime.utcnow().isoformat()
        systems.append({"id": i, "name": name, "status": status, "last_updated": last_updated})
    return {"systems": systems}

@app.get("/api/mock_scenarios")
async def get_mock_scenarios(user=Depends(get_current_user), db=Depends(get_db)):
    from apps.backend.models import Incident

    incidents = db.query(Incident).order_by(Incident.created_at.desc()).limit(50).all()
    if incidents:
        out = []
        for inc in incidents:
            agentic_state = "after" if inc.status in ("resolved", "closed") else "before"
            out.append({
                "incident_id": inc.incident_id,
                "scenario_label": inc.type or "Incident",
                "agentic_state": agentic_state,
                "title": inc.title or "",
                "description": inc.description or "",
                "severity": inc.severity or "medium",
                "status": inc.status or "open",
                "type": inc.type or "incident",
                "desk": inc.desk or "",
                "trader": inc.trader or "",
                "priority": inc.priority or 2,
                "created_at": inc.created_at.isoformat() if inc.created_at else "",
                "updated_at": inc.updated_at.isoformat() if inc.updated_at else "",
            })
        return out

    use_demo = os.getenv("USE_DEMO_FALLBACK", "true").lower() == "true"
    if not use_demo:
        return []
    now = datetime.utcnow()
    return [
        {"incident_id": "INC-001", "scenario_label": "Stuck Order", "agentic_state": "before",
         "title": "Stuck Order (Before)", "description": "Order stuck in pending.", "severity": "high",
         "status": "open", "type": "stuck_order", "desk": "FX", "trader": "alice", "priority": 1,
         "created_at": (now - timedelta(minutes=10)).isoformat(), "updated_at": (now - timedelta(minutes=10)).isoformat()},
        {"incident_id": "INC-002", "scenario_label": "Stuck Order", "agentic_state": "after",
         "title": "Stuck Order (After)", "description": "Remediated by agent.", "severity": "high",
         "status": "resolved", "type": "stuck_order", "desk": "FX", "trader": "alice", "priority": 1,
         "created_at": (now - timedelta(minutes=10)).isoformat(), "updated_at": (now - timedelta(minutes=5)).isoformat()},
    ]

def _get_audit_trail_entries(db, entity_type=None, event_type=None, regulation_tag=None, start=None, end=None, limit=100):
    """Fetch audit trail from audit_trail table, with optional filters."""
    from apps.backend.models import AuditTrailEntry, User

    query = db.query(AuditTrailEntry).order_by(AuditTrailEntry.timestamp.desc())
    if entity_type:
        query = query.filter(AuditTrailEntry.entity_type == entity_type)
    if event_type:
        query = query.filter(AuditTrailEntry.event_type == event_type)
    if start:
        from dateutil.parser import parse
        query = query.filter(AuditTrailEntry.timestamp >= parse(start))
    if end:
        from dateutil.parser import parse
        query = query.filter(AuditTrailEntry.timestamp <= parse(end))
    rows = query.limit(limit * 2 if regulation_tag else limit).all()
    if regulation_tag:
        rows = [r for r in rows if r.regulation_tags and regulation_tag in r.regulation_tags][:limit]
    entries = []
    for r in rows:
        user_name = "System"
        if r.actor_type == "human" and r.actor_id:
            u = db.query(User).filter(User.id == r.actor_id).first()
            user_name = u.email.split("@")[0] if u and u.email else str(r.actor_id)
        elif r.actor_type == "agent":
            user_name = "Agent"
        tags = r.regulation_tags or []
        compliance_tag = tags[0] if tags else "SEC 17a-4"
        if compliance_tag == "SEC_17a4":
            compliance_tag = "SEC 17a-4"
        elif compliance_tag == "FINRA_4511":
            compliance_tag = "FINRA 4511"
        entries.append({
            "timestamp": r.timestamp.isoformat() if r.timestamp else "",
            "action": (r.event_type or "event").replace("_", " ").title(),
            "user": user_name,
            "details": r.summary or "",
            "compliance_tag": compliance_tag,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "regulation_tags": r.regulation_tags or [],
        })
    return entries


@app.get("/api/audit_trail")
async def get_audit_trail(
    entity_type: str = None,
    event_type: str = None,
    regulation_tag: str = None,
    start: str = None,
    end: str = None,
    limit: int = 100,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Unified audit trail from audit_trail table. Supports filtering."""
    entries = _get_audit_trail_entries(db, entity_type, event_type, regulation_tag, start, end, limit)
    if not entries and os.getenv("USE_DEMO_FALLBACK", "true").lower() == "true":
        return [
            {"timestamp": "2024-06-10T09:01:00Z", "action": "Incident Detected", "user": "Agent", "details": "Stuck order flagged", "compliance_tag": "SEC 17a-4", "entity_type": "incident", "entity_id": None, "regulation_tags": ["SEC_17a4"]},
            {"timestamp": "2024-06-10T09:01:05Z", "action": "Triage Started", "user": "Agent", "details": "AI agent classified severity: High", "compliance_tag": "FINRA 4511", "entity_type": "agent_action", "entity_id": None, "regulation_tags": ["FINRA_4511"]},
        ]
    return entries


@app.get("/api/mock_audit_trail")
async def get_mock_audit_trail(user=Depends(get_current_user), db=Depends(get_db)):
    """Deprecated: use /api/audit_trail instead. Returns same data for backward compatibility."""
    return await get_audit_trail(user=user, db=db)


@app.get("/api/audit_trail/export")
async def export_audit_trail(
    format: str = "csv",
    entity_type: str = None,
    event_type: str = None,
    start: str = None,
    end: str = None,
    limit: int = 1000,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Export audit trail as CSV or JSON for compliance evidence."""
    from fastapi.responses import StreamingResponse
    from io import StringIO
    import csv as csv_module
    from apps.backend.models import AuditTrailEntry

    try:
        from apps.backend.services.audit_trail_service import record_audit_event
        user_id = getattr(user, "id", None) if hasattr(user, "id") else None
        record_audit_event(
            db=db,
            event_type="export_initiated",
            entity_type="export",
            entity_id="audit_trail_export",
            actor_type="human",
            actor_id=user_id,
            summary=f"Audit trail export initiated ({format})",
            details={"format": format, "entity_type": entity_type, "event_type": event_type},
            regulation_tags=["SEC_17a4"],
        )
    except Exception:
        pass

    query = db.query(AuditTrailEntry).order_by(AuditTrailEntry.timestamp.desc())
    if entity_type:
        query = query.filter(AuditTrailEntry.entity_type == entity_type)
    if event_type:
        query = query.filter(AuditTrailEntry.event_type == event_type)
    if start:
        from dateutil.parser import parse
        query = query.filter(AuditTrailEntry.timestamp >= parse(start))
    if end:
        from dateutil.parser import parse
        query = query.filter(AuditTrailEntry.timestamp <= parse(end))
    rows = query.limit(limit).all()
    if format == "csv":
        output = StringIO()
        fieldnames = ["id", "timestamp", "event_type", "entity_type", "entity_id", "actor_type", "actor_id", "summary", "regulation_tags"]
        writer = csv_module.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "id": r.id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                "event_type": r.event_type,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "actor_type": r.actor_type,
                "actor_id": r.actor_id,
                "summary": r.summary,
                "regulation_tags": str(r.regulation_tags) if r.regulation_tags else "",
            })
        output.seek(0)
        content = output.getvalue()
        import hashlib
        import base64
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        headers_out = {
            "Content-Disposition": "attachment; filename=audit_trail.csv",
            "X-Content-SHA256": content_hash,
        }
        try:
            from apps.backend import crypto_utils
            sig = crypto_utils.sign_data(content_hash.encode("utf-8"))
            headers_out["X-Content-Signature"] = base64.b64encode(sig).decode("ascii")
        except Exception:
            pass
        return StreamingResponse(
            iter([content]),
            media_type="text/csv",
            headers=headers_out,
        )
    import json as json_module
    import hashlib
    import base64
    from fastapi.responses import Response

    json_data = [{"id": r.id, "timestamp": r.timestamp.isoformat() if r.timestamp else "", "event_type": r.event_type, "entity_type": r.entity_type, "entity_id": r.entity_id, "actor_type": r.actor_type, "summary": r.summary, "regulation_tags": r.regulation_tags} for r in rows]
    json_str = json_module.dumps(json_data, default=str)
    content_hash = hashlib.sha256(json_str.encode("utf-8")).hexdigest()
    headers_out = {
        "Content-Disposition": "attachment; filename=audit_trail.json",
        "X-Content-SHA256": content_hash,
    }
    try:
        from apps.backend import crypto_utils
        sig = crypto_utils.sign_data(content_hash.encode("utf-8"))
        headers_out["X-Content-Signature"] = base64.b64encode(sig).decode("ascii")
    except Exception:
        pass
    return Response(
        content=json_str,
        media_type="application/json",
        headers=headers_out,
    )
