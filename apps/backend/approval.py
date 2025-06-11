from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .models import Base, User


class ApprovalStatus(enum.Enum):
    # Enum for approval status values. Used to track the current state of an
    # approval request for sensitive actions and exports.
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    escalated = "escalated"


class ApprovalRequest(Base):
    """
    SQLAlchemy ORM model for approval requests. Each request tracks the status
    and metadata for a sensitive action or export that requires privileged
    approval.

    Fields:
        id: Primary key.
        resource_type: Type of resource (e.g., 'export', 'incident',
            'compliance').
        resource_id: Unique identifier for the resource.
        requested_by: User ID of the requester.
        status: Current approval status (pending, approved, rejected, escalated).
        reason: Reason for the approval request.
        decision_by: User ID of the decider (nullable).
        decision_reason: Reason provided for decision (nullable).
        created_at: Timestamp when request was created.
        decided_at: Timestamp when decision was made (nullable).
        meta: Additional metadata (JSON, nullable).
    """

    __tablename__ = "approval_requests"
    id = Column(Integer, primary_key=True)
    resource_type = Column(String, index=True)  # e.g., 'export', 'incident',
    # 'compliance'
    resource_id = Column(String, index=True)
    requested_by = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.pending)
    reason = Column(String)
    decision_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    decision_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)
    meta = Column(JSON, nullable=True)

    requester = relationship("User", foreign_keys=[requested_by])
    decider = relationship("User", foreign_keys=[decision_by])


def require_approval(db, resource_type, resource_id, user_id, reason=None, meta=None):
    """
    Checks for an existing pending approval for the given resource and user. If
    none exists, creates a new approval request. Returns a tuple:

        (approved: bool, approval_request: ApprovalRequest or None)

    If an approved request already exists for this resource and user, returns
    (True, approval_request). If a pending request exists, returns (False,
    approval_request). Otherwise, creates a new pending request and returns
    (False, new_request).

    Args:
        db: SQLAlchemy session.
        resource_type: The type of resource (e.g., 'export', 'incident').
        resource_id: The unique identifier for the resource.
        user_id: The ID of the user requesting approval.
        reason: (Optional) Reason for the approval request.
        meta: (Optional) Additional metadata as a dict.

    Returns:
        Tuple[bool, ApprovalRequest or None]
    """
    from .approval import ApprovalRequest, ApprovalStatus

    req = (
        db.query(ApprovalRequest)
        .filter_by(
            resource_type=resource_type,
            resource_id=resource_id,
            requested_by=user_id,
            status=ApprovalStatus.pending,
        )
        .first()
    )
    if req:
        return False, req
    # Check if already approved
    req_approved = (
        db.query(ApprovalRequest)
        .filter_by(
            resource_type=resource_type,
            resource_id=resource_id,
            requested_by=user_id,
            status=ApprovalStatus.approved,
        )
        .first()
    )
    if req_approved:
        return True, req_approved
    # Create new approval request
    new_req = ApprovalRequest(
        resource_type=resource_type,
        resource_id=resource_id,
        requested_by=user_id,
        status=ApprovalStatus.pending,
        reason=reason,
        meta=meta,
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return False, new_req
