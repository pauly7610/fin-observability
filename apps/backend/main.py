from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from apps.backend.database import engine, Base
from apps.backend.routers import (
    agent, ops, ops_trigger, audit, compliance, incidents, transactions, system_metrics, users, compliance_lcr, verification, anomaly, export_metadata
)
from apps.backend.scheduled_exports import schedule_exports
from apscheduler.schedulers.background import BackgroundScheduler
from apps.backend.agentic_escalation import escalate_overdue_agent_actions
from apps.backend.database import SessionLocal

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)
otlp_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

app = FastAPI(
    title="Financial AI Observability Platform",
    description="Backend API for financial services observability and automation",
    version="0.1.0"
)

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
scheduler.add_job(escalation_job, 'interval', hours=1, id='agentic_escalation')
scheduler.start()

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 