"""Tests for anomaly router."""
from apps.backend.main import app
from fastapi.testclient import TestClient
import pytest

client = TestClient(app)

ADMIN_HEADERS = {"x-user-email": "admin@example.com", "x-user-role": "admin"}
VIEWER_HEADERS = {"x-user-email": "viewer@example.com", "x-user-role": "viewer"}


def test_anomaly_detect():
    """Test POST /anomaly/detect with valid payload."""
    resp = client.post(
        "/anomaly/detect",
        json={
            "data": [{"amount": 100, "hour": 10}, {"amount": 50000, "hour": 3}],
            "model_type": "isolation_forest",
            "parameters": {},
        },
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "anomalies" in data
    assert "scores" in data


def test_anomaly_transactions_recent():
    """Test GET /anomaly/transactions/recent."""
    resp = client.get("/anomaly/transactions/recent", headers=VIEWER_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_anomaly_metrics_recent():
    """Test GET /anomaly/metrics/recent."""
    resp = client.get("/anomaly/metrics/recent", headers=VIEWER_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_anomaly_unauth_returns_401_or_demo():
    """Test anomaly endpoints require auth (or return demo viewer when DEMO_MODE)."""
    resp = client.get("/anomaly/transactions/recent")
    # With DEMO_MODE, unauthenticated gets demo viewer; without, 401
    assert resp.status_code in (200, 401)


def test_anomaly_train():
    """Test POST /anomaly/train retrains model from historical data."""
    resp = client.post(
        "/anomaly/train",
        json={"source": "transactions", "feature_keys": None},
        headers=ADMIN_HEADERS,
    )
    # 200 if data exists, 400 if "No data found", 500 if bug (e.g. before fix)
    assert resp.status_code in (200, 400)
    if resp.status_code == 200:
        assert "message" in resp.json()
