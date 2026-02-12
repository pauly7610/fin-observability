from typing import Any, Dict, List
from langchain.tools import Tool
from .base_agent import BaseAgent
import logging
import os
import json
import httpx

logger = logging.getLogger(__name__)


def _get_base_url() -> str:
    return os.getenv("FIN_OBSERVABILITY_API_URL", "http://localhost:8000")


def _get_headers() -> dict:
    """Auth headers for backend API calls."""
    token = os.getenv("FIN_OBSERVABILITY_API_TOKEN")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {
        "x-user-email": os.getenv("FIN_OBSERVABILITY_USER_EMAIL", "admin@finobs.io"),
        "x-user-role": os.getenv("FIN_OBSERVABILITY_USER_ROLE", "admin"),
    }


class IncidentTriageAgent(BaseAgent):
    def __init__(
        self,
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0.0,
        verbose: bool = False,
        base_url: str = None,
    ):
        self._base_url = base_url or _get_base_url()
        tools = [
            Tool(
                name="analyze_incident",
                func=self._analyze_incident,
                description="Analyze an incident and determine its severity and potential impact"
            ),
            Tool(
                name="get_similar_incidents",
                func=self._get_similar_incidents,
                description="Find similar historical incidents for reference"
            ),
            Tool(
                name="suggest_remediation",
                func=self._suggest_remediation,
                description="Suggest remediation steps based on incident details"
            ),
            Tool(
                name="update_incident_status",
                func=self._update_incident_status,
                description="Update the status of an incident"
            )
        ]
        super().__init__(
            tools=tools,
            model_name=model_name,
            temperature=temperature,
            verbose=verbose
        )
        self.prompt = self.prompt.messages[0].content = """
        You are an AI assistant specialized in financial services incident triage.
        Your role is to:
        1. Analyze incidents and determine their severity
        2. Find similar historical incidents
        3. Suggest appropriate remediation steps
        4. Help update incident status

        Always consider:
        - Financial impact
        - Regulatory compliance
        - Customer impact
        - System stability
        - Security implications
        """

    def _analyze_incident(self, x: Any) -> Dict[str, Any]:
        """Analyze incident via backend API."""
        incident = x if isinstance(x, dict) else (json.loads(x) if isinstance(x, str) else {})
        if not isinstance(incident, dict):
            incident = {"incident": incident}
        if "incident" not in incident:
            incident = {"incident": incident}
        try:
            r = httpx.post(
                f"{self._base_url}/incidents/analyze",
                json=incident,
                headers=_get_headers(),
                timeout=30.0,
            )
            r.raise_for_status()
            data = r.json()
            return data.get("result", data)
        except Exception as e:
            logger.error(f"Error analyzing incident: {str(e)}")
            return {"severity": "unknown", "risk_score": 0, "recommended_actions": ["Manual review required"]}

    def _get_similar_incidents(self, x: Any) -> List[Dict[str, Any]]:
        """Find similar incidents via backend API."""
        data = x if isinstance(x, dict) else (json.loads(x) if isinstance(x, str) else {})
        if not isinstance(data, dict):
            data = {"incident": data}
        if "incident" not in data:
            data = {"incident": data, "limit": data.get("limit", 5)}
        data.setdefault("limit", 5)
        try:
            r = httpx.post(
                f"{self._base_url}/incidents/similar",
                json=data,
                headers=_get_headers(),
                timeout=30.0,
            )
            r.raise_for_status()
            return r.json().get("similar", [])
        except Exception as e:
            logger.error(f"Error finding similar incidents: {str(e)}")
            return []

    def _suggest_remediation(self, x: Any) -> List[Dict[str, Any]]:
        """Suggest remediation via backend API."""
        incident = x if isinstance(x, dict) else (json.loads(x) if isinstance(x, str) else {})
        if not isinstance(incident, dict):
            incident = {"incident": incident}
        if "incident" not in incident:
            incident = {"incident": incident}
        try:
            r = httpx.post(
                f"{self._base_url}/incidents/remediation",
                json=incident,
                headers=_get_headers(),
                timeout=30.0,
            )
            r.raise_for_status()
            data = r.json()
            return data.get("steps", [{"step": 1, "action": data.get("result", {}).get("recommendation", "Manual review"), "priority": "high", "estimated_time": "N/A"}])
        except Exception as e:
            logger.error(f"Error suggesting remediation: {str(e)}")
            return [{"step": 1, "action": "Manual review required", "priority": "high", "estimated_time": "N/A"}]

    def _update_incident_status(self, x: Any) -> Dict[str, Any]:
        """Update incident status via backend API."""
        data = x if isinstance(x, dict) else (json.loads(x) if isinstance(x, str) else {})
        incident_id = data.get("incident_id") or data.get("incident")
        new_status = data.get("new_status") or data.get("status")
        notes = data.get("notes")
        if not incident_id or not new_status:
            return {"error": "Missing incident_id or status"}
        try:
            r = httpx.patch(
                f"{self._base_url}/incidents/{incident_id}/status",
                json={"status": new_status, "notes": notes},
                headers=_get_headers(),
                timeout=30.0,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"Error updating incident status: {str(e)}")
            return {"incident_id": incident_id, "status": new_status, "error": str(e)}