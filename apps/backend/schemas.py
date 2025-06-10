from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

# Transaction schemas
class TransactionBase(BaseModel):
    amount: float
    currency: str
    meta: Dict[str, Any]

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int
    transaction_id: str
    timestamp: datetime
    status: str
    is_anomaly: bool
    anomaly_score: Optional[float] = None
    anomaly_details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# Compliance log schemas
class ComplianceLogBase(BaseModel):
    event_type: str
    event_id: str
    severity: str
    description: str
    meta: Dict[str, Any]

class ComplianceLogCreate(ComplianceLogBase):
    pass

class ComplianceLog(ComplianceLogBase):
    id: int
    timestamp: datetime
    is_resolved: bool
    resolution_notes: Optional[str] = None

    class Config:
        from_attributes = True

# System metric schemas
class SystemMetricBase(BaseModel):
    metric_name: str
    value: float
    labels: Dict[str, str]

class SystemMetricCreate(SystemMetricBase):
    pass

class SystemMetric(SystemMetricBase):
    id: int
    timestamp: datetime
    is_anomaly: bool
    anomaly_score: Optional[float] = None

    class Config:
        from_attributes = True

# Incident schemas
class IncidentBase(BaseModel):
    title: str
    description: str
    severity: str
    meta: Dict[str, Any]

class IncidentCreate(IncidentBase):
    pass

class Incident(IncidentBase):
    id: int
    incident_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    assigned_to: Optional[int] = None

    class Config:
        from_attributes = True

# Agent action schemas
class AgentActionBase(BaseModel):
    incident_id: str
    action: str
    agent_result: str
    meta: dict = {}
    assigned_to: int = None
    is_escalated: bool = False
    escalated_at: datetime = None
    escalation_reason: str = None
    approvals_required: int = 1
    approvals: list = []
    is_fully_approved: bool = False
    fully_approved_at: datetime = None
    approval_roles: list = []
    approval_order: list = []
    current_approval_index: int = 0
    # Agentic explainability and attribution fields
    ai_explanation: str = None
    agent_input: dict = None
    agent_output: dict = None
    agent_version: str = None
    actor_type: str = None
    is_simulation: bool = False

class AgentActionCreate(AgentActionBase):
    submitted_by: int

class AgentActionUpdate(BaseModel):
    status: str
    approved_by: int = None
    approved_at: datetime = None
    meta: dict = {}
    assigned_to: int = None
    is_escalated: bool = None
    escalated_at: datetime = None
    escalation_reason: str = None
    approvals_required: int = None
    approvals: list = None
    is_fully_approved: bool = None
    fully_approved_at: datetime = None
    approval_roles: list = None
    approval_order: list = None
    current_approval_index: int = None
    # Agentic explainability and attribution fields
    ai_explanation: str = None
    agent_input: dict = None
    agent_output: dict = None
    agent_version: str = None
    actor_type: str = None
    override_type: str = None
    is_simulation: bool = None

class AgentAction(AgentActionBase):
    id: int
    status: str
    submitted_by: int = None
    approved_by: int = None
    created_at: datetime
    approved_at: datetime = None
    assigned_to: int = None
    is_escalated: bool = False
    escalated_at: datetime = None
    escalation_reason: str = None
    approvals_required: int = 1
    approvals: list = []
    is_fully_approved: bool = False
    fully_approved_at: datetime = None
    approval_roles: list = []
    approval_order: list = []
    current_approval_index: int = 0
    override_type: str = None

    class Config:
        from_attributes = True

# Agent action audit log schemas
class AgentActionAuditLogBase(BaseModel):
    event_type: str
    from_status: str = None
    to_status: str = None
    operator_id: int = None
    comment: str = None
    meta: dict = None
    # Agentic audit fields
    ai_explanation: str = None
    agent_input: dict = None
    agent_output: dict = None
    agent_version: str = None
    actor_type: str = None
    override_type: str = None
    is_simulation: bool = False

# Export metadata schemas
class ExportMetadataBase(BaseModel):
    export_type: str
    file_path: str
    hash: str
    signature: str = None
    requested_by: int = None
    delivered_to: str = None
    delivery_method: str = None
    delivery_status: str = "pending"
    verification_status: str = "unverified"
    created_at: datetime = None
    delivered_at: datetime = None
    verified_at: datetime = None
    meta: dict = None

class ExportMetadataCreate(ExportMetadataBase):
    pass

class ExportMetadata(ExportMetadataBase):
    id: int
    class Config:
        from_attributes = True

class AgentActionAuditLogCreate(AgentActionAuditLogBase):
    agent_action_id: int

class AgentActionAuditLog(AgentActionAuditLogBase):
    id: int
    agent_action_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# Anomaly detection schemas
class AnomalyDetectionRequest(BaseModel):
    data: List[Dict[str, Any]]
    model_type: str = Field(..., description="Type of anomaly detection model to use")
    model_config = {'protected_namespaces': ()}
    parameters: Optional[Dict[str, Any]] = None

class AnomalyDetectionResponse(BaseModel):
    anomalies: List[Dict[str, Any]]
    scores: List[float]
    model_meta: Dict[str, Any] 