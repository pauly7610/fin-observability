"""Tests for incidents router."""
from apps.backend.main import app
from fastapi.testclient import TestClient
import pytest

client = TestClient(app)

ADMIN_HEADERS = {"x-user-email": "admin@example.com", "x-user-role": "admin"}
ANALYST_HEADERS = {"x-user-email": "analyst@example.com", "x-user-role": "analyst"}


def test_list_incidents():
    """Test GET /incidents returns { incidents: [...] }."""
    resp = client.get("/incidents", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "incidents" in data
    assert isinstance(data["incidents"], list)


def test_bulk_resolve():
    """Test POST /incidents/bulk/resolve."""
    resp = client.post(
        "/incidents/bulk/resolve",
        json={"incident_ids": []},
        headers=ANALYST_HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data


def test_bulk_assign():
    """Test POST /incidents/bulk/assign."""
    resp = client.post(
        "/incidents/bulk/assign",
        json={"incident_ids": [], "assigned_to": 1},
        headers=ANALYST_HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
