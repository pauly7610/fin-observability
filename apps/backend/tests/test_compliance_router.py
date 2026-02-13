"""Tests for compliance router."""
from apps.backend.main import app
from fastapi.testclient import TestClient
import pytest

client = TestClient(app)

ADMIN_HEADERS = {"x-user-email": "admin@example.com", "x-user-role": "admin"}
VIEWER_HEADERS = {"x-user-email": "viewer@example.com", "x-user-role": "viewer"}


def test_get_compliance_logs():
    """Test GET /compliance/logs with auth."""
    resp = client.get("/compliance/logs", headers=VIEWER_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_get_compliance_logs_with_filters():
    """Test GET /compliance/logs with query params."""
    resp = client.get("/compliance/logs?limit=5", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) <= 5
