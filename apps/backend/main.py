from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from opentelemetry import trace

from apps.backend.broadcast import incident_broadcaster
from apps.backend.database import engine, SessionLocal
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

# Mount MCP server for AI agent integration
try:
    from apps.backend.mcp_server import mcp as mcp_instance, get_usage_stats
    mcp_app = mcp_instance.streamable_http_app()
    app.mount("/mcp", mcp_app)
    logging.getLogger(__name__).info("MCP server mounted at /mcp")

    @app.get("/mcp/stats", tags=["mcp"])
    async def mcp_stats():
        """Get MCP tool usage statistics."""
        return get_usage_stats()

    @app.get("/mcp/tools", tags=["mcp"])
    async def mcp_tools():
        """Get list of available MCP tools with descriptions."""
        tools = mcp_instance._tool_manager.list_tools()
        return {
            "endpoint": "https://fin-observability-production.up.railway.app/mcp",
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
except Exception as e:
    logging.getLogger(__name__).warning(f"MCP server failed to mount: {e}")

# Instrument FastAPI with OpenTelemetry
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)

# Custom metrics middleware
app.middleware("http")(metrics_middleware)

# Demo mode: block write operations for unauthenticated (viewer) users
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

# Safe POST endpoints that viewers can use (read-like operations)
DEMO_SAFE_POSTS = {
    "/agent/compliance/monitor",
    "/agent/compliance/explain",
    "/agent/compliance/explain-batch",
    "/agent/compliance/test-batch",
    "/agent/compliance/ensemble",
}

@app.middleware("http")
async def demo_write_guard(request: Request, call_next):
    """Block write operations for demo/viewer users to prevent data poisoning."""
    if not DEMO_MODE:
        return await call_next(request)

    method = request.method.upper()
    if method in ("GET", "HEAD", "OPTIONS"):
        return await call_next(request)

    # Allow safe POST endpoints (read-like ML inference) and MCP
    path = request.url.path.rstrip("/")
    if path in DEMO_SAFE_POSTS or path.startswith("/mcp"):
        return await call_next(request)

    # Check if user is authenticated (has auth headers, bearer token, or webhook key)
    has_auth = (
        request.headers.get("x-user-email")
        or request.headers.get("authorization")
        or request.headers.get("x-webhook-key")
        or request.query_params.get("key")
    )
    if has_auth:
        return await call_next(request)

    # Unauthenticated write → block
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=403,
        content={"detail": "Demo mode: write operations require authentication. Read-only access for visitors."},
    )

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


@app.websocket("/ws/incidents")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time incident updates.
    Clients receive JSON strings with new/updated incidents.
    """
    await websocket.accept()
    await incident_broadcaster.connect(websocket)
    try:
        test_incident = {
            "incident_id": "TEST-001",
            "title": "Test Incident",
            "description": "This is a test incident",
            "severity": "high",
            "status": "open",
            "type": "test",
            "created_at": datetime.utcnow().isoformat()
        }
        await websocket.send_json(test_incident)
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
    """
    await websocket.accept()
    try:
        # Send some test data immediately
        test_compliance = {
            "type": "compliance_update",
            "status": "active",
            "message": "Test compliance update",
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket.send_json(test_compliance)
        
        while True:
            await websocket.receive_text()  # keepalive
    except WebSocketDisconnect:
        pass


@app.get("/api/metrics")
async def get_platform_metrics():
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
async def get_kafka_status():
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
async def get_systems():
    # Return some test data in an object with a 'systems' property
    return {
        "systems": [
            {
                "id": 1,
                "name": "Trading System",
                "status": "operational",
                "last_updated": datetime.utcnow().isoformat()
            },
            {
                "id": 2,
                "name": "Risk Management",
                "status": "operational",
                "last_updated": datetime.utcnow().isoformat()
            }
        ]
    }

@app.get("/api/mock_scenarios")
async def get_mock_scenarios():
    now = datetime.utcnow()
    return [
        {
            "incident_id": "INC-001",
            "scenario_label": "Stuck Order",
            "agentic_state": "before",
            "title": "Stuck Order (Before Agentic Intervention)",
            "description": "Order #12345 stuck in pending state. No agentic action taken yet.",
            "severity": "high",
            "status": "open",
            "type": "stuck_order",
            "desk": "FX",
            "trader": "alice",
            "priority": 1,
            "created_at": (now - timedelta(minutes=10)).isoformat(),
            "updated_at": (now - timedelta(minutes=10)).isoformat()
        },
        {
            "incident_id": "INC-002",
            "scenario_label": "Stuck Order",
            "agentic_state": "after",
            "title": "Stuck Order (After Agentic Intervention)",
            "description": "Order #12345 automatically remediated by agent. All actions logged.",
            "severity": "high",
            "status": "resolved",
            "type": "stuck_order",
            "desk": "FX",
            "trader": "alice",
            "priority": 1,
            "created_at": (now - timedelta(minutes=10)).isoformat(),
            "updated_at": (now - timedelta(minutes=5)).isoformat()
        },
        {
            "incident_id": "INC-003",
            "scenario_label": "Latency Spike",
            "agentic_state": "before",
            "title": "Latency Spike (Before Agentic Intervention)",
            "description": "Latency spike detected, no action taken yet.",
            "severity": "medium",
            "status": "investigating",
            "type": "latency_spike",
            "desk": "Equities",
            "trader": "bob",
            "priority": 2,
            "created_at": (now - timedelta(minutes=20)).isoformat(),
            "updated_at": (now - timedelta(minutes=20)).isoformat()
        },
        {
            "incident_id": "INC-004",
            "scenario_label": "Latency Spike",
            "agentic_state": "after",
            "title": "Latency Spike (After Agentic Intervention)",
            "description": "AI agent isolated root cause, triggered automated fix, and logged the event.",
            "severity": "medium",
            "status": "resolved",
            "type": "latency_spike",
            "desk": "Equities",
            "trader": "bob",
            "priority": 2,
            "created_at": (now - timedelta(minutes=20)).isoformat(),
            "updated_at": (now - timedelta(minutes=15)).isoformat()
        }
    ]

@app.get("/api/mock_audit_trail")
async def get_mock_audit_trail():
    return [
        {
            "timestamp": "2024-06-10T09:01:00Z",
            "action": "Incident Detected",
            "user": "Agent",
            "details": "Stuck order flagged on FX desk",
            "compliance_tag": "SEC 17a-4"
        },
        {
            "timestamp": "2024-06-10T09:01:05Z",
            "action": "Triage Started",
            "user": "Agent",
            "details": "AI agent classified severity: High",
            "compliance_tag": "FINRA 4511"
        },
        {
            "timestamp": "2024-06-10T09:01:10Z",
            "action": "Remediation Executed",
            "user": "Agent",
            "details": "Order router restarted",
            "compliance_tag": "SEC 17a-4"
        },
        {
            "timestamp": "2024-06-10T09:01:15Z",
            "action": "Human Approval",
            "user": "Analyst",
            "details": "Approved agent recommendation",
            "compliance_tag": "FINRA 4511"
        },
        {
            "timestamp": "2024-06-10T09:01:20Z",
            "action": "Audit Trail Exported",
            "user": "Compliance",
            "details": "Evidence package generated for regulator",
            "compliance_tag": "SEC 17a-4"
        }
    ]
