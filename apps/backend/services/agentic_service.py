from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

# In-memory store for demo agentic tasks (replace with DB or queue in prod)
_agentic_tasks = {}


# --- SUGGESTIONS ---
def get_agentic_suggestions(incident: dict) -> List[Dict[str, Any]]:
    """
    Return a list of agentic actions relevant to the incident type/status.
    Covers typical investment bank trading ops workflows.
    """
    suggestions = []
    # --- Order Management ---
    if incident.get("status") == "open" and incident.get("type") in [
        "order_failure",
        "stuck_order",
    ]:
        suggestions.append(
            {
                "action_type": "auto_retry_order",
                "label": "Auto-Retry Order",
                "description": "Automatically retry failed or stuck order.",
                "parameters": {"order_id": incident.get("order_id")},
            }
        )
        suggestions.append(
            {
                "action_type": "cancel_order",
                "label": "Cancel Order",
                "description": "Cancel the problematic order.",
                "parameters": {"order_id": incident.get("order_id")},
            }
        )
        suggestions.append(
            {
                "action_type": "escalate_to_desk_lead",
                "label": "Escalate to Desk Lead",
                "description": "Escalate this incident to the trading desk lead for review.",
                "parameters": {},
            }
        )
    # --- Position Reconciliation ---
    if incident.get("type") == "position_break":
        suggestions.append(
            {
                "action_type": "reconcile_position",
                "label": "Reconcile Position",
                "description": "Launch agentic reconciliation workflow for position breaks.",
                "parameters": {"account": incident.get("account")},
            }
        )
    # --- Risk Controls ---
    if incident.get("type") == "risk_limit_breach":
        suggestions.append(
            {
                "action_type": "block_trader",
                "label": "Block Trader",
                "description": "Block the trader from further activity.",
                "parameters": {"trader_id": incident.get("trader_id")},
            }
        )
        suggestions.append(
            {
                "action_type": "escalate_to_risk_desk",
                "label": "Escalate to Risk Desk",
                "description": "Escalate this risk event to the risk desk.",
                "parameters": {},
            }
        )
    # --- Settlement ---
    if incident.get("type") == "settlement_failure":
        suggestions.append(
            {
                "action_type": "auto_retry_settlement",
                "label": "Auto-Retry Settlement",
                "description": "Automatically retry failed settlement.",
                "parameters": {"settlement_id": incident.get("settlement_id")},
            }
        )
        suggestions.append(
            {
                "action_type": "notify_counterparty",
                "label": "Notify Counterparty",
                "description": "Send notification to counterparty for failed settlement.",
                "parameters": {"counterparty": incident.get("counterparty")},
            }
        )
    # --- Escalation/Comms ---
    suggestions.append(
        {
            "action_type": "notify_compliance",
            "label": "Notify Compliance",
            "description": "Send notification to compliance team.",
            "parameters": {},
        }
    )
    suggestions.append(
        {
            "action_type": "send_slack_alert",
            "label": "Send Slack Alert",
            "description": "Send a Slack alert to the ops channel.",
            "parameters": {"incident_id": incident.get("incident_id")},
        }
    )
    return suggestions


# --- EXECUTION ---
import asyncio
import random
from typing import Optional


def execute_agentic_action(
    incident_id: str, action_type: str, parameters: Optional[dict] = None
) -> str:
    """
    Simulate running an agentic action asynchronously. Returns a task_id.
    The action will be marked as 'running' initially, then after a short delay,
    will be randomly marked as 'succeeded' or 'failed' (10% failure rate).
    """
    task_id = str(uuid.uuid4())
    _agentic_tasks[task_id] = {
        "incident_id": incident_id,
        "action_type": action_type,
        "parameters": parameters or {},
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
        "result": None,
        "finished_at": None,
    }
    # Start async simulation in background
    asyncio.create_task(
        _simulate_agentic_action(task_id, incident_id, action_type, parameters or {})
    )
    return task_id


async def _simulate_agentic_action(
    task_id: str, incident_id: str, action_type: str, parameters: dict
):
    """
    Simulate agentic action completion and broadcast WebSocket notifications on status change.
    Notification structure:
    {
        "type": "agentic_action_status",
        "task_id": str,
        "incident_id": str,
        "action_type": str,
        "status": str,  # running/succeeded/failed
        "result": str or None,
        "finished_at": str or None
    }
    """
    import json
    from apps.backend.main import incident_broadcaster

    await asyncio.sleep(random.uniform(1.0, 2.5))  # Simulate processing delay
    fail = random.random() < 0.1  # 10% chance to fail
    if fail:
        status = "failed"
        result = f"Agentic action '{action_type}' failed due to a simulated error."
    else:
        status = "succeeded"
        # Simulate different results for each action_type
        if action_type == "auto_retry_order":
            result = f"Order {parameters.get('order_id', '')} retried successfully."
        elif action_type == "cancel_order":
            result = f"Order {parameters.get('order_id', '')} cancelled."
        elif action_type == "reconcile_position":
            result = f"Position for account {parameters.get('account', '')} reconciled."
        elif action_type == "block_trader":
            result = f"Trader {parameters.get('trader_id', '')} blocked."
        elif action_type == "escalate_to_desk_lead":
            result = "Incident escalated to desk lead."
        elif action_type == "escalate_to_risk_desk":
            result = "Incident escalated to risk desk."
        elif action_type == "auto_retry_settlement":
            result = f"Settlement {parameters.get('settlement_id', '')} retried."
        elif action_type == "notify_counterparty":
            result = f"Counterparty {parameters.get('counterparty', '')} notified."
        elif action_type == "notify_compliance":
            result = "Compliance team notified."
        elif action_type == "send_slack_alert":
            result = (
                f"Slack alert sent for incident {parameters.get('incident_id', '')}."
            )
        else:
            result = f"Agentic action '{action_type}' completed."
    _agentic_tasks[task_id].update(
        {
            "status": status,
            "result": result,
            "finished_at": datetime.utcnow().isoformat(),
        }
    )
    # Broadcast WebSocket notification
    notification = {
        "type": "agentic_action_status",
        "task_id": task_id,
        "incident_id": incident_id,
        "action_type": action_type,
        "status": status,
        "result": result,
        "finished_at": _agentic_tasks[task_id]["finished_at"],
    }
    await incident_broadcaster.broadcast(json.dumps(notification))


# --- STATUS ---
def get_agentic_action_status(task_id: str) -> Optional[dict]:
    return _agentic_tasks.get(task_id)
