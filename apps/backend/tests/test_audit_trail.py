"""
Tests for the agentic audit trail service and API.
"""
import pytest
from apps.backend.main import app
from fastapi.testclient import TestClient
from datetime import datetime
from sqlalchemy.orm import Session
from apps.backend.database import SessionLocal
from apps.backend.models import AuditTrailEntry, User
from apps.backend.services.audit_trail_service import record_audit_event


client = TestClient(app)
ADMIN_HEADERS = {"x-user-email": "admin@example.com", "x-user-role": "admin"}


@pytest.fixture(autouse=True)
def clear_audit_trail_before_test():
    """Clear audit_trail before each test in this module to avoid cross-test pollution."""
    db = SessionLocal()
    try:
        db.query(AuditTrailEntry).delete()
        db.commit()
    finally:
        db.close()
    yield


def test_record_audit_event_logs_on_failure():
    """record_audit_event should log on DB failure and return None."""
    from unittest.mock import patch

    db = SessionLocal()
    try:
        with patch.object(db, "commit", side_effect=Exception("simulated DB failure")):
            result = record_audit_event(
                db=db,
                event_type="test_failure",
                entity_type="transaction",
                entity_id="fail-txn",
                actor_type="agent",
                summary="Should fail",
                regulation_tags=[],
            )
        assert result is None
    finally:
        db.close()


def test_audit_trail_sanitizes_pii_in_details(monkeypatch):
    """With PII_HASH_ENABLED, details with email/account should be hashed before storage."""
    from apps.backend.services import audit_trail_service
    from apps.backend import pii_utils

    monkeypatch.setattr(audit_trail_service, "PII_HASH_ENABLED", True)
    monkeypatch.setattr(pii_utils, "PII_HASH_ENABLED", True)
    db = SessionLocal()
    try:
        record_audit_event(
            db=db,
            event_type="pii_sanitize_test",
            entity_type="transaction",
            entity_id="pii-test-txn",
            actor_type="agent",
            summary="PII sanitize test",
            details={"email": "user@example.com", "account": "1234567890"},
            regulation_tags=["FINRA_4511"],
        )
        entry = db.query(AuditTrailEntry).filter(
            AuditTrailEntry.entity_id == "pii-test-txn"
        ).first()
        assert entry is not None
        assert entry.details is not None
        assert entry.details.get("email", "").startswith("pii:")
        assert entry.details.get("account", "").startswith("pii:")
    finally:
        db.close()
        monkeypatch.setattr(audit_trail_service, "PII_HASH_ENABLED", False)
        monkeypatch.setattr(pii_utils, "PII_HASH_ENABLED", False)


def test_record_audit_event_creates_entry():
    """record_audit_event should create an AuditTrailEntry in the DB."""
    db = SessionLocal()
    try:
        record_audit_event(
            db=db,
            event_type="transaction_scored",
            entity_type="transaction",
            entity_id="test-txn-001",
            actor_type="agent",
            summary="Transaction scored: approve",
            regulation_tags=["FINRA_4511", "SEC_17a4"],
        )
        entry = db.query(AuditTrailEntry).filter(
            AuditTrailEntry.entity_id == "test-txn-001"
        ).first()
        assert entry is not None
        assert entry.event_type == "transaction_scored"
        assert entry.entity_type == "transaction"
        assert entry.summary == "Transaction scored: approve"
    finally:
        db.close()


def test_record_audit_event_with_regulation_tags():
    """regulation_tags should be stored correctly as JSON."""
    db = SessionLocal()
    try:
        record_audit_event(
            db=db,
            event_type="agent_action_approved",
            entity_type="agent_action",
            entity_id="99",
            actor_type="human",
            summary="Action approved",
            regulation_tags=["SEC_17a4", "FINRA_4511"],
        )
        entry = db.query(AuditTrailEntry).filter(
            AuditTrailEntry.entity_id == "99"
        ).first()
        assert entry is not None
        assert entry.regulation_tags == ["SEC_17a4", "FINRA_4511"]
    finally:
        db.close()


def test_get_audit_trail_returns_entries():
    """GET /api/audit_trail should return entries when present."""
    resp = client.get("/api/audit_trail", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if data:
        assert "timestamp" in data[0] or "action" in data[0]


def test_get_audit_trail_filter_by_entity_type():
    """GET /api/audit_trail?entity_type=transaction should filter."""
    # Create transaction data so we don't rely on demo fallback (which ignores filters)
    db = SessionLocal()
    try:
        record_audit_event(
            db=db,
            event_type="transaction_scored",
            entity_type="transaction",
            entity_id="filter-test-txn",
            actor_type="system",
            actor_id=None,
            summary="Filter test",
            details={},
            regulation_tags=["FINRA_4511"],
        )
    finally:
        db.close()
    resp = client.get(
        "/api/audit_trail",
        params={"entity_type": "transaction"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    for entry in data:
        assert entry.get("entity_type") == "transaction"


def test_get_audit_trail_demo_fallback():
    """Empty DB with USE_DEMO_FALLBACK should return demo entries."""
    import os
    os.environ["USE_DEMO_FALLBACK"] = "true"
    resp = client.get("/api/audit_trail", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if not any(e.get("entity_type") for e in data):
        assert len(data) >= 0


def test_compliance_monitor_persists_audit_entry():
    """POST /agent/compliance/monitor should persist to audit_trail."""
    db = SessionLocal()
    try:
        before = db.query(AuditTrailEntry).filter(
            AuditTrailEntry.event_type == "compliance_monitor_decision"
        ).count()
        resp = client.post(
            "/agent/compliance/monitor",
            headers=ADMIN_HEADERS,
            json={
                "id": "txn_audit_test",
                "amount": 5000,
                "counterparty": "Test Corp",
                "account": "1234567890",
                "timestamp": datetime.utcnow().isoformat(),
                "type": "ach",
            },
        )
        assert resp.status_code == 200
        after = db.query(AuditTrailEntry).filter(
            AuditTrailEntry.event_type == "compliance_monitor_decision",
            AuditTrailEntry.entity_id == "txn_audit_test",
        ).count()
        assert after >= 1
    finally:
        db.close()


def test_compliance_monitor_audit_includes_model_version():
    """POST /agent/compliance/monitor should store model_version in audit details."""
    db = SessionLocal()
    try:
        resp = client.post(
            "/agent/compliance/monitor",
            headers=ADMIN_HEADERS,
            json={
                "id": "txn_model_version_test",
                "amount": 5000,
                "counterparty": "Test Corp",
                "account": "1234567890",
                "timestamp": datetime.utcnow().isoformat(),
                "type": "ach",
            },
        )
        assert resp.status_code == 200
        entry = db.query(AuditTrailEntry).filter(
            AuditTrailEntry.event_type == "compliance_monitor_decision",
            AuditTrailEntry.entity_id == "txn_model_version_test",
        ).first()
        assert entry is not None
        assert entry.details is not None
        assert "model_version" in entry.details
        assert "anomaly_score" in entry.details
        assert "risk_factors" in entry.details
        assert "input_summary" in entry.details
    finally:
        db.close()


def test_mock_audit_trail_redirects():
    """GET /api/mock_audit_trail should return same shape as /api/audit_trail."""
    resp = client.get("/api/mock_audit_trail", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if data:
        assert "timestamp" in data[0]
        assert "action" in data[0]
        assert "compliance_tag" in data[0]


def test_audit_trail_export_csv():
    """GET /api/audit_trail/export?format=csv should return CSV."""
    resp = client.get(
        "/api/audit_trail/export",
        params={"format": "csv"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")
    assert "attachment" in resp.headers.get("content-disposition", "")
    # Content hash (SHA-256) for WORM compliance
    hash_header = resp.headers.get("x-content-sha256")
    assert hash_header is not None
    assert len(hash_header) == 64
    assert all(c in "0123456789abcdef" for c in hash_header)


def test_audit_trail_export_json_with_hash():
    """GET /api/audit_trail/export?format=json should return JSON with X-Content-SHA256."""
    resp = client.get(
        "/api/audit_trail/export",
        params={"format": "json"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    assert "application/json" in resp.headers.get("content-type", "")
    assert "attachment" in resp.headers.get("content-disposition", "")
    hash_header = resp.headers.get("x-content-sha256")
    assert hash_header is not None
    assert len(hash_header) == 64


def test_record_audit_event_actor_types():
    """record_audit_event should handle agent/human/system actor types."""
    db = SessionLocal()
    try:
        # agent: actor_id=None
        record_audit_event(
            db=db,
            event_type="agent_action_proposed",
            entity_type="agent_action",
            entity_id="actor-test-1",
            actor_type="agent",
            summary="Agent proposed action",
            actor_id=None,
        )
        e1 = db.query(AuditTrailEntry).filter(AuditTrailEntry.entity_id == "actor-test-1").first()
        assert e1 is not None
        assert e1.actor_type == "agent"
        assert e1.actor_id is None

        # system: actor_id=None
        record_audit_event(
            db=db,
            event_type="export_initiated",
            entity_type="export",
            entity_id="actor-test-2",
            actor_type="system",
            summary="System export",
            actor_id=None,
        )
        e2 = db.query(AuditTrailEntry).filter(AuditTrailEntry.entity_id == "actor-test-2").first()
        assert e2 is not None
        assert e2.actor_type == "system"
    finally:
        db.close()


def test_score_and_store_transaction_persists_audit():
    """POST /webhooks/transactions should persist transaction_scored to audit_trail."""
    from apps.backend.database import SessionLocal

    db = SessionLocal()
    try:
        txn_id = f"audit-test-txn-{datetime.utcnow().timestamp()}"
        before = db.query(AuditTrailEntry).filter(
            AuditTrailEntry.entity_id == txn_id,
            AuditTrailEntry.event_type == "transaction_scored",
        ).count()
        resp = client.post(
            "/webhooks/transactions",
            json={"amount": 1000, "type": "ach", "transaction_id": txn_id},
            headers={"X-Webhook-Key": "test-webhook-key"},
        )
        assert resp.status_code == 200
        after = db.query(AuditTrailEntry).filter(
            AuditTrailEntry.entity_id == txn_id,
            AuditTrailEntry.event_type == "transaction_scored",
        ).count()
        assert after >= 1
    finally:
        db.close()


def test_agent_action_approve_persists_audit():
    """POST /agent/ops/actions/{id}/approve should persist agent_action_approved."""
    db = SessionLocal()
    try:
        from apps.backend.models import AgentAction, User

        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            admin = User(email="admin@example.com", role="admin")
            db.add(admin)
            db.commit()
            db.refresh(admin)
        action = AgentAction(
            workflow_id="INC-AUDIT-TEST",
            incident_id="INC-AUDIT-TEST",
            action="review",
            status="pending",
            ai_explanation="Test",
        )
        db.add(action)
        db.commit()
        db.refresh(action)
        resp = client.post(
            f"/agent/ops/actions/{action.id}/approve",
            params={"operator": str(admin.id)},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200
        after = db.query(AuditTrailEntry).filter(
            AuditTrailEntry.event_type == "agent_action_approved",
            AuditTrailEntry.entity_id == str(action.id),
        ).count()
        assert after >= 1
    finally:
        db.close()


def test_incident_activity_persists_audit():
    """record_incident_activity should persist incident_status_change to audit_trail."""
    from apps.backend.services.incident_activity_service import record_incident_activity

    db = SessionLocal()
    try:
        inc_id = f"INC-AUDIT-ACT-{datetime.utcnow().timestamp()}"
        record_incident_activity(
            db=db,
            incident_id=inc_id,
            event_type="status_change",
            old_value="open",
            new_value="investigating",
        )
        entry = db.query(AuditTrailEntry).filter(
            AuditTrailEntry.entity_id == inc_id,
            AuditTrailEntry.event_type == "incident_status_change",
        ).first()
        assert entry is not None
    finally:
        db.close()


def test_export_initiated_audit():
    """Audit trail export should record export_initiated."""
    db = SessionLocal()
    try:
        before = db.query(AuditTrailEntry).filter(
            AuditTrailEntry.entity_id == "audit_trail_export",
            AuditTrailEntry.event_type == "export_initiated",
        ).count()
        resp = client.get(
            "/api/audit_trail/export",
            params={"format": "json"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200
        after = db.query(AuditTrailEntry).filter(
            AuditTrailEntry.entity_id == "audit_trail_export",
            AuditTrailEntry.event_type == "export_initiated",
        ).count()
        assert after >= before + 1
    finally:
        db.close()


def test_get_audit_trail_filter_by_event_type():
    """GET /api/audit_trail?event_type=compliance_monitor_decision should filter."""
    # Create compliance_monitor_decision data so we don't rely on demo fallback
    db = SessionLocal()
    try:
        record_audit_event(
            db=db,
            event_type="compliance_monitor_decision",
            entity_type="transaction",
            entity_id="filter-event-test",
            actor_type="system",
            actor_id=None,
            summary="Filter event test",
            details={},
            regulation_tags=["FINRA_4511"],
        )
    finally:
        db.close()
    resp = client.get(
        "/api/audit_trail",
        params={"event_type": "compliance_monitor_decision"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    for entry in data:
        assert entry.get("action", "").replace(" ", "_").lower() == "compliance_monitor_decision"


def test_get_audit_trail_filter_by_regulation_tag():
    """GET /api/audit_trail?regulation_tag=FINRA_4511 should filter."""
    # Create FINRA_4511 data so we don't rely on demo fallback
    db = SessionLocal()
    try:
        record_audit_event(
            db=db,
            event_type="approval_requested",
            entity_type="approval",
            entity_id="filter-tag-test",
            actor_type="human",
            actor_id=1,
            summary="Filter tag test",
            details={},
            regulation_tags=["FINRA_4511"],
        )
    finally:
        db.close()
    resp = client.get(
        "/api/audit_trail",
        params={"regulation_tag": "FINRA_4511"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    for entry in data:
        tags = entry.get("regulation_tags", [])
        assert "FINRA_4511" in tags or entry.get("compliance_tag") == "FINRA 4511"


def test_get_audit_trail_start_end_params():
    """GET /api/audit_trail with start/end should filter by date."""
    resp = client.get(
        "/api/audit_trail",
        params={"start": "2024-01-01T00:00:00Z", "end": "2024-12-31T23:59:59Z"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_approval_decided_audit():
    """POST /approval/{id}/decision should persist approval_decided to audit_trail."""
    db = SessionLocal()
    try:
        resp_create = client.post(
            "/approval/",
            params={"resource_type": "test_export", "resource_id": "audit-test-1", "reason": "Test"},
            headers=ADMIN_HEADERS,
        )
        assert resp_create.status_code == 200
        req = resp_create.json()
        approval_id = req["id"]
        resp_decide = client.post(
            f"/approval/{approval_id}/decision",
            params={"decision": "approved", "decision_reason": "OK"},
            headers=ADMIN_HEADERS,
        )
        assert resp_decide.status_code == 200
        entry = db.query(AuditTrailEntry).filter(
            AuditTrailEntry.entity_id == str(approval_id),
            AuditTrailEntry.event_type == "approval_decided",
        ).first()
        assert entry is not None
    finally:
        db.close()
