import logging
import socket
import json
import requests

# SIEM syslog integration (UDP, RFC5424)
def send_syslog_event(message: str, host: str, port: int = 514):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    syslog_msg = f"<134>{message}"
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
