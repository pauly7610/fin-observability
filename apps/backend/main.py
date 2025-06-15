from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from apps.backend.routers import approval
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from apps.backend.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from apps.backend.broadcast import incident_broadcaster
from apps.backend.database import engine, Base
import logging
import structlog
from opentelemetry import trace
from datetime import datetime


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

# Instrument database for tracing
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

SQLAlchemyInstrumentor().instrument(engine=engine)

# Instrument HTTP clients for tracing
from opentelemetry.instrumentation.requests import RequestsInstrumentor

RequestsInstrumentor().instrument()
try:
    from opentelemetry.instrumentation.boto3s3 import Boto3S3Instrumentor

    Boto3S3Instrumentor().instrument()
except ImportError:
    pass  # boto3 S3 instrumentation is optional and only if boto3 is present
from apps.backend.routers import (
    agent,
    ops,
    ops_trigger,
    audit,
    compliance,
    incidents,
    transactions,
    system_metrics,
    users,
    compliance_lcr,
    verification,
    anomaly,
    export_metadata,
    ops_metrics,
)


# --- Incident WebSocket Broadcaster ---
class IncidentBroadcaster:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)




app = FastAPI()


@app.websocket("/ws/incidents")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time incident updates.
    Clients receive JSON strings with new/updated incidents.
    """
    await websocket.accept()
    await incident_broadcaster.connect(websocket)
    try:
        # Send some test data immediately
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


from apps.backend.scheduled_exports import schedule_exports
from apscheduler.schedulers.background import BackgroundScheduler
from apps.backend.agentic_escalation import escalate_overdue_agent_actions
from apps.backend.database import SessionLocal

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize OpenTelemetry (tracing)
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)
otlp_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Initialize OpenTelemetry Metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.metrics import set_meter_provider, get_meter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

metric_exporter = OTLPMetricExporter(endpoint="localhost:4317", insecure=True)
metric_reader = PeriodicExportingMetricReader(metric_exporter)
meter_provider = MeterProvider(metric_readers=[metric_reader])
set_meter_provider(meter_provider)

# Define meters for key business/compliance events
metrics_meter = get_meter(__name__)
export_job_counter = metrics_meter.create_counter(
    name="export_jobs_total",
    description="Total export jobs run",
)
compliance_action_counter = metrics_meter.create_counter(
    name="compliance_actions_total",
    description="Total compliance actions performed",
)
anomaly_detected_counter = metrics_meter.create_counter(
    name="anomalies_detected_total",
    description="Total anomalies detected",
)

app = FastAPI(
    title="Financial AI Observability Platform",
    description="Backend API for financial services observability and automation",
    version="0.1.0",
)
app.include_router(approval.router)

app.state.limiter = limiter
from slowapi import _rate_limit_exceeded_handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
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
app.include_router(compliance_lcr.router)
app.include_router(verification.router)

# Instrument FastAPI with OpenTelemetry
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)

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
scheduler.start()

# Limiter is now created below and imported by routers


@app.get("/health")
@limiter.limit("5/minute")  # Example: 5 requests per minute per IP
async def health_check(request):
    return {"status": "healthy"}


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
