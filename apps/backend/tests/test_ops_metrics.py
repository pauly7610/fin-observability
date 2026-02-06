from apps.backend.main import app
from fastapi.testclient import TestClient
import pytest

client = TestClient(app)


def test_mttr_empty():
    resp = client.get(
        "/ops_metrics/mttr?days=1",
        headers={"x-user-email": "admin@example.com", "x-user-role": "admin"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "mttr_hours" in data
    assert "resolved_count" in data


def test_agentic_action_rate_empty():
    resp = client.get(
        "/ops_metrics/agentic_action_rate?days=1",
        headers={"x-user-email": "admin@example.com", "x-user-role": "admin"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "agentic_action_count" in data
    assert data["days"] == 1


def test_sla_compliance_empty():
    resp = client.get(
        "/ops_metrics/sla_compliance?sla_hours=4&days=1",
        headers={"x-user-email": "admin@example.com", "x-user-role": "admin"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "sla_compliance_pct" in data
    assert "resolved_count" in data
