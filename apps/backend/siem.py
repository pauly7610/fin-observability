import logging
import socket
import json
import requests
from opentelemetry import trace

# SIEM syslog integration (UDP, RFC5424)
def send_syslog_event(event: str, host: str = "localhost", port: int = 514, extra: dict = None):
    """
    Send a syslog event to the configured SIEM server, structured as JSON and including trace/span IDs if available.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tracer = trace.get_current_span()
    trace_id = None
    span_id = None
    if tracer and hasattr(tracer, 'get_span_context'):
        ctx = tracer.get_span_context()
        trace_id = getattr(ctx, 'trace_id', None)
        span_id = getattr(ctx, 'span_id', None)
    event_dict = {
        "event": event,
        "trace_id": format(trace_id, 'x') if trace_id else None,
        "span_id": format(span_id, 'x') if span_id else None,
    }
    if extra:
        event_dict.update(extra)
    syslog_msg = json.dumps(event_dict)
    sock.sendto(syslog_msg.encode(), (host, port))
    sock.close()

# SIEM HTTP integration (e.g. ELK HTTP endpoint)
def send_http_event(event: dict, url: str, api_key: str = None):
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(event))
        resp.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to send SIEM event: {e}")

# Example usage:
# send_syslog_event("Agent action exported", host="splunk.company.com", port=514)
# send_http_event({"event": "Agent action exported"}, url="https://elk.company.com/ingest")
