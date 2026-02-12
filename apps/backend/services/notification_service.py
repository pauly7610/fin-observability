"""
Incident notification service - Slack and generic webhook integration.
"""
import os
import logging
import httpx

logger = logging.getLogger(__name__)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
INCIDENT_WEBHOOK_URL = os.getenv("INCIDENT_WEBHOOK_URL", "")
INCIDENT_NOTIFY_MIN_PRIORITY = int(os.getenv("INCIDENT_NOTIFY_MIN_PRIORITY", "1"))


def send_incident_notification(incident) -> bool:
    """
    Send incident notification to Slack and/or generic webhook.
    Returns True if at least one notification was sent successfully.
    """
    try:
        priority = getattr(incident, "priority", 99)
        if priority > INCIDENT_NOTIFY_MIN_PRIORITY:
            return False

        incident_id = getattr(incident, "incident_id", "unknown")
        title = getattr(incident, "title", "Incident")
        severity = getattr(incident, "severity", "unknown")
        status = getattr(incident, "status", "open")
        incident_type = getattr(incident, "type", "")
        desk = getattr(incident, "desk", "")
        trader = getattr(incident, "trader", "")

        payload = {
            "incident_id": incident_id,
            "title": title,
            "severity": severity,
            "priority": priority,
            "status": status,
            "type": incident_type,
            "desk": desk,
            "trader": trader,
        }

        sent = False

        if SLACK_WEBHOOK_URL:
            slack_blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"Incident: {incident_id}", "emoji": True},
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Title:*\n{title}"},
                        {"type": "mrkdwn", "text": f"*Severity:*\n{severity}"},
                        {"type": "mrkdwn", "text": f"*Status:*\n{status}"},
                        {"type": "mrkdwn", "text": f"*Type:*\n{incident_type or 'N/A'}"},
                    ],
                },
            ]
            if desk or trader:
                slack_blocks.append({
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": f"Desk: {desk or 'N/A'} | Trader: {trader or 'N/A'}"}],
                })
            try:
                r = httpx.post(
                    SLACK_WEBHOOK_URL,
                    json={"blocks": slack_blocks, "text": f"Incoming incident: {incident_id}"},
                    timeout=10.0,
                )
                if r.status_code == 200:
                    sent = True
                else:
                    logger.warning(f"Slack webhook returned {r.status_code}: {r.text}")
            except Exception as e:
                logger.error(f"Slack notification failed: {e}")

        if INCIDENT_WEBHOOK_URL:
            try:
                r = httpx.post(
                    INCIDENT_WEBHOOK_URL,
                    json=payload,
                    timeout=10.0,
                )
                if r.status_code in (200, 201, 202, 204):
                    sent = True
                else:
                    logger.warning(f"Incident webhook returned {r.status_code}: {r.text}")
            except Exception as e:
                logger.error(f"Incident webhook failed: {e}")

        return sent
    except Exception as e:
        logger.error(f"send_incident_notification failed: {e}")
        return False
