from typing import Dict, Any, List
from langchain.tools import Tool
from .base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

class IncidentTriageAgent(BaseAgent):
    def __init__(
        self,
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0.0,
        verbose: bool = False
    ):
        # Define tools for incident triage
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
        
        # Override the system prompt for incident triage
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

    def _analyze_incident(self, incident_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze an incident and determine its severity and potential impact.
        """
        try:
            # This would typically call the backend API
            # For now, return a mock analysis
            return {
                "severity": "high",
                "impact_areas": ["transactions", "compliance"],
                "risk_score": 0.8,
                "recommended_actions": [
                    "Notify compliance team",
                    "Review affected transactions",
                    "Check system logs"
                ]
            }
        except Exception as e:
            logger.error(f"Error analyzing incident: {str(e)}")
            raise

    def _get_similar_incidents(
        self,
        incident_details: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar historical incidents for reference.
        """
        try:
            # This would typically call the backend API
            # For now, return mock similar incidents
            return [
                {
                    "incident_id": "INC-001",
                    "title": "Similar incident 1",
                    "severity": "high",
                    "resolution": "Resolved by system restart"
                }
            ]
        except Exception as e:
            logger.error(f"Error finding similar incidents: {str(e)}")
            raise

    def _suggest_remediation(
        self,
        incident_details: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Suggest remediation steps based on incident details.
        """
        try:
            # This would typically call the backend API
            # For now, return mock remediation steps
            return [
                {
                    "step": 1,
                    "action": "Isolate affected systems",
                    "priority": "high",
                    "estimated_time": "5 minutes"
                },
                {
                    "step": 2,
                    "action": "Review system logs",
                    "priority": "high",
                    "estimated_time": "15 minutes"
                }
            ]
        except Exception as e:
            logger.error(f"Error suggesting remediation: {str(e)}")
            raise

    def _update_incident_status(
        self,
        incident_id: str,
        new_status: str,
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Update the status of an incident.
        """
        try:
            # This would typically call the backend API
            # For now, return mock update confirmation
            return {
                "incident_id": incident_id,
                "status": new_status,
                "updated_at": "2024-03-14T12:00:00Z",
                "notes": notes
            }
        except Exception as e:
            logger.error(f"Error updating incident status: {str(e)}")
            raise 