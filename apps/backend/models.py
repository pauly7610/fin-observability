from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class IncidentActivity(Base):
    __tablename__ = "incident_activities"
    id = Column(Integer, primary_key=True)
    incident_id = Column(String, ForeignKey("incidents.incident_id"), index=True)
    event_type = Column(
        String, nullable=False
    )  # comment, status_change, assignment, escalation, etc.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    old_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    comment = Column(String, nullable=True)
    meta = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String)  # "admin", "analyst", "compliance"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True)
    amount = Column(Float)
    currency = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String)  # "pending", "completed", "failed"
    meta = Column(JSON)
    is_anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Float, nullable=True)
    anomaly_details = Column(JSON, nullable=True)


class ComplianceLog(Base):
    __tablename__ = "compliance_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String)  # "transaction", "system", "user_action"
    event_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    severity = Column(String)  # "low", "medium", "high", "critical"
    description = Column(String)
    meta = Column(JSON)
    is_resolved = Column(Boolean, default=False)
    resolution_notes = Column(String, nullable=True)


class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String, index=True)
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    labels = Column(JSON)
    is_anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Float, nullable=True)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(String)
    severity = Column(String)  # "low", "medium", "high", "critical"
    status = Column(String)  # "open", "investigating", "resolved", "closed"
    type = Column(String, index=True)  # 'stuck_order', 'missed_trade', 'spike', etc.
    desk = Column(String, index=True)
    trader = Column(String, index=True)
    priority = Column(Integer, index=True)
    root_cause = Column(String, nullable=True)
    recommended_action = Column(String, nullable=True)
    source_event_id = Column(String, nullable=True)
    detection_method = Column(String, nullable=True)  # 'rule', 'ml', 'manual', etc.
    last_event_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    meta = Column(JSON)

    assigned_user = relationship("User")


class AgentAction(Base):
    __tablename__ = "agent_actions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String, index=True)  # groups actions for a workflow/incident
    parent_action_id = Column(
        Integer, ForeignKey("agent_actions.id"), nullable=True
    )  # links to previous action
    incident_id = Column(String, index=True)
    action = Column(String)
    agent_result = Column(String)
    status = Column(String, default="pending")  # pending, approved, rejected
    auto_approved = Column(Boolean, default=False)  # True if auto-remediated
    submitted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    meta = Column(JSON)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_escalated = Column(Boolean, default=False)
    escalated_at = Column(DateTime, nullable=True)
    escalation_reason = Column(String, nullable=True)
    approvals_required = Column(Integer, default=1)
    approvals = Column(JSON, default=list)
    is_fully_approved = Column(Boolean, default=False)
    fully_approved_at = Column(DateTime, nullable=True)
    approval_roles = Column(JSON, default=list)  # e.g., ["admin", "compliance"]
    approval_order = Column(JSON, default=list)  # e.g., [user_id1, user_id2]
    current_approval_index = Column(Integer, default=0)

    # Agentic explainability and attribution fields
    ai_explanation = Column(
        String, nullable=True
    )  # Reasoning or explanation from agent/AI
    agent_input = Column(JSON, nullable=True)  # Input provided to agent/AI
    agent_output = Column(JSON, nullable=True)  # Full output from agent/AI
    agent_version = Column(String, nullable=True)  # Version of agent/AI/model
    actor_type = Column(String, nullable=True)  # 'human', 'agent', 'system'
    is_simulation = Column(Boolean, default=False)  # True if this was a simulation/test

    submitter = relationship("User", foreign_keys=[submitted_by])
    approver = relationship("User", foreign_keys=[approved_by])
    parent_action = relationship(
        "AgentAction", remote_side=[id], foreign_keys=[parent_action_id]
    )
    assignee = relationship("User", foreign_keys=[assigned_to])


class AgentActionAuditLog(Base):
    __tablename__ = "agent_action_audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    agent_action_id = Column(Integer, ForeignKey("agent_actions.id"), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(
        String
    )  # created, approved, rejected, assigned, commented, escalated, etc.
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    comment = Column(String, nullable=True)
    meta = Column(JSON, nullable=True)
    # Agentic audit fields
    ai_explanation = Column(String, nullable=True)
    agent_input = Column(JSON, nullable=True)
    agent_output = Column(JSON, nullable=True)
    agent_version = Column(String, nullable=True)
    actor_type = Column(String, nullable=True)
    override_type = Column(
        String, nullable=True
    )  # e.g., 'ai_override', 'manual_override', etc.
    is_simulation = Column(Boolean, default=False)
    operator = relationship("User", foreign_keys=[operator_id])
    agent_action = relationship("AgentAction", foreign_keys=[agent_action_id])


class ExportMetadata(Base):
    __tablename__ = "export_metadata"
    id = Column(Integer, primary_key=True, index=True)
    export_type = Column(String, index=True)  # e.g., compliance_log, agent_action, etc.
    file_path = Column(String)
    hash = Column(String)
    signature = Column(String)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    delivered_to = Column(String)  # email or S3 path
    delivery_method = Column(String)  # email, s3, etc.
    delivery_status = Column(String, default="pending")  # pending, delivered, failed
    verification_status = Column(
        String, default="unverified"
    )  # unverified, verified, tampered, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    meta = Column(JSON, nullable=True)
    requester = relationship("User", foreign_keys=[requested_by])


class ComplianceFeedback(Base):
    __tablename__ = "compliance_feedback"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, index=True, nullable=False)
    predicted_action = Column(String, nullable=False)  # approve, block, manual_review
    actual_action = Column(String, nullable=False)  # approve, block, manual_review
    is_correct = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=True)
    anomaly_score = Column(Float, nullable=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    reviewer = relationship("User", foreign_keys=[reviewer_id])
