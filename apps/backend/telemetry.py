"""
OpenTelemetry instrumentation for the Financial Observability Platform.

Initializes tracing (OTLP → Grafana Cloud / Collector) and metrics
(counters, histograms) used across the application. Supports both
direct-to-Grafana and OTel Collector modes via environment variables.

Environment variables:
    OTEL_SERVICE_NAME           — Service name for traces/metrics (default: fin-observability)
    OTEL_EXPORTER_OTLP_ENDPOINT — Collector endpoint (overridden when Grafana creds are set)
    GRAFANA_CLOUD_INSTANCE_ID   — Grafana Cloud instance ID (enables direct OTLP)
    GRAFANA_CLOUD_API_TOKEN     — Grafana Cloud API token
"""
import base64
import logging
import os
import time

from fastapi import Request
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.metrics import set_meter_provider, get_meter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

# Module-level references used by routers via `from apps.backend.telemetry import ...`
export_job_counter = None
compliance_action_counter = None
anomaly_detected_counter = None
http_request_counter = None
http_request_duration = None
audit_trail_write_failures_counter = None


def _build_otlp_config():
    """Resolve OTLP endpoint and auth headers from environment."""
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    instance_id = os.environ.get("GRAFANA_CLOUD_INSTANCE_ID")
    api_token = os.environ.get("GRAFANA_CLOUD_API_TOKEN")

    headers = {}
    if instance_id and api_token:
        credentials = base64.b64encode(f"{instance_id}:{api_token}".encode()).decode()
        headers["Authorization"] = f"Basic {credentials}"
        endpoint = "https://otlp-gateway-prod-us-east-3.grafana.net/otlp"
        logging.info(f"Grafana Cloud OTLP auth configured for instance {instance_id}")
    elif endpoint and not endpoint.startswith("http"):
        endpoint = f"http://{endpoint}"

    return endpoint, headers


def init_tracing(resource: Resource, endpoint: str, headers: dict):
    """Configure TracerProvider and OTLP span exporter."""
    trace.set_tracer_provider(TracerProvider(resource=resource))

    if endpoint:
        exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces", headers=headers)
        trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(exporter))
        logging.info(f"OTLP trace exporter enabled -> {endpoint}")
    else:
        logging.info("OTEL_EXPORTER_OTLP_ENDPOINT not set — OTLP trace exporter disabled")


def init_metrics(resource: Resource, endpoint: str, headers: dict):
    """Configure MeterProvider, OTLP metric exporter, and application counters."""
    global export_job_counter, compliance_action_counter, anomaly_detected_counter
    global http_request_counter, http_request_duration, audit_trail_write_failures_counter

    if endpoint:
        exporter = OTLPMetricExporter(endpoint=f"{endpoint}/v1/metrics", headers=headers)
        reader = PeriodicExportingMetricReader(exporter)
        provider = MeterProvider(resource=resource, metric_readers=[reader])
        logging.info(f"OTLP metric exporter enabled -> {endpoint}")
    else:
        logging.info("OTEL_EXPORTER_OTLP_ENDPOINT not set — OTLP metric exporter disabled")
        provider = MeterProvider(resource=resource)

    set_meter_provider(provider)

    meter = get_meter(__name__)
    export_job_counter = meter.create_counter(
        name="export_jobs_total",
        description="Total export jobs run",
    )
    compliance_action_counter = meter.create_counter(
        name="compliance_actions_total",
        description="Total compliance actions performed",
    )
    anomaly_detected_counter = meter.create_counter(
        name="anomalies_detected_total",
        description="Total anomalies detected",
    )
    http_request_counter = meter.create_counter(
        name="http_requests_total",
        description="Total HTTP requests",
    )
    http_request_duration = meter.create_histogram(
        name="http_request_duration_ms",
        description="HTTP request duration in milliseconds",
        unit="ms",
    )
    audit_trail_write_failures_counter = meter.create_counter(
        name="audit_trail_write_failures_total",
        description="Total audit trail write failures",
    )


def init_telemetry():
    """One-call entry point: sets up tracing + metrics from environment."""
    service_name = os.environ.get("OTEL_SERVICE_NAME", "fin-observability")
    resource = Resource.create({"service.name": service_name})
    endpoint, headers = _build_otlp_config()

    init_tracing(resource, endpoint, headers)
    init_metrics(resource, endpoint, headers)


async def metrics_middleware(request: Request, call_next):
    """Record HTTP request count and duration for every request."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    route = request.url.path
    method = request.method
    status = str(response.status_code)
    http_request_counter.add(1, {"http_method": method, "http_route": route, "http_status_code": status})
    http_request_duration.record(duration_ms, {"http_method": method, "http_route": route, "http_status_code": status})
    return response
