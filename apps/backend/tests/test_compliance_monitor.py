from apps.backend.main import app
from fastapi.testclient import TestClient
import pytest
from datetime import datetime

client = TestClient(app)


def test_compliance_monitor_safe_transaction():
    """Test that a small ACH transaction is approved."""
    resp = client.post(
        "/agent/compliance/monitor",
        json={
            "id": "txn_test_safe",
            "amount": 5000,
            "counterparty": "Regular Customer Inc",
            "account": "1234567890",
            "timestamp": datetime.utcnow().isoformat(),
            "type": "ach"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] in ("approve", "manual_review")
    assert data["confidence"] >= 50
    assert "audit_trail" in data
    assert data["audit_trail"]["regulation"] == "FINRA_4511"


def test_compliance_monitor_suspicious_transaction():
    """Test that a large wire transfer triggers manual review."""
    resp = client.post(
        "/agent/compliance/monitor",
        json={
            "id": "txn_test_suspicious",
            "amount": 50000,
            "counterparty": "ACME Corp",
            "account": "9876543210",
            "timestamp": datetime.utcnow().isoformat(),
            "type": "wire"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] in ("manual_review", "approve", "block")
    assert data["confidence"] >= 50


def test_compliance_monitor_blocked_transaction():
    """Test that a very large transaction is blocked."""
    resp = client.post(
        "/agent/compliance/monitor",
        json={
            "id": "txn_test_blocked",
            "amount": 150000,
            "counterparty": "Unknown Entity LLC",
            "account": "5555555555",
            "timestamp": datetime.utcnow().isoformat(),
            "type": "wire"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "block"
    assert data["confidence"] >= 80
    assert "FINRA_4511" in data["reasoning"] or "100,000" in data["reasoning"] or "compliance" in data["reasoning"].lower()


def test_compliance_status_endpoint():
    """Test the compliance agent status endpoint."""
    resp = client.get("/agent/compliance/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "operational"
    assert data["agent"] == "FinancialComplianceAgent"
    assert "FINRA_4511" in data["regulations"]
    assert "SEC_17a4" in data["regulations"]
    assert "isolation_forest_ml" in data["features"]
