"""Tests for MCP server and compliance check endpoint."""
from apps.backend.main import app
from fastapi.testclient import TestClient
import pytest
from datetime import datetime

client = TestClient(app)

ADMIN_HEADERS = {"x-user-email": "admin@example.com", "x-user-role": "admin"}


def test_api_compliance_check():
    """Test POST /api/compliance/check returns MCP-shaped response."""
    resp = client.post(
        "/api/compliance/check",
        json={
            "amount": 5000,
            "transaction_type": "wire_transfer",
            "timestamp": datetime.utcnow().isoformat(),
            "transaction_id": "test-mcp-001",
        },
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "decision" in data
    assert data["decision"] in ("approve", "manual_review")
    assert "confidence" in data
    assert "anomaly_score" in data
    assert "risk_level" in data
    assert "transaction_id" in data
    assert data["transaction_id"] == "test-mcp-001"


def test_api_compliance_check_missing_amount():
    """Test POST /api/compliance/check returns 400 when amount is missing."""
    resp = client.post(
        "/api/compliance/check",
        json={"transaction_type": "wire"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 400


def test_api_compliance_check_invalid_amount():
    """Test POST /api/compliance/check returns 400 for invalid amount."""
    resp = client.post(
        "/api/compliance/check",
        json={"amount": -100, "transaction_type": "wire"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 400


def test_mcp_tools_list():
    """Test GET /mcp/tools returns tool list."""
    resp = client.get("/mcp/tools", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "tools" in data
    assert "endpoint" in data
    assert "tool_count" in data
    tool_names = [t["name"] for t in data["tools"]]
    assert "check_transaction_compliance" in tool_names


def test_mcp_stats():
    """Test GET /mcp/stats returns usage stats."""
    resp = client.get("/mcp/stats", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_calls" in data
    assert "tools" in data
    assert "avg_latency_ms" in data
