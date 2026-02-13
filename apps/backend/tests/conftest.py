"""
Pytest configuration for backend tests.
Sets env vars required for tests (webhook key, header auth, SQLite for CI).
"""
import os
import pytest

# Set before any app imports so webhooks, security, and database read correct values
os.environ.setdefault("WEBHOOK_API_KEY", "test-webhook-key")
os.environ.setdefault("TRUST_HEADER_AUTH", "true")
os.environ.setdefault("REGISTER_ENABLED", "true")
# Use SQLite for tests when Postgres is not available
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
# WebSocket auth disabled for tests (no token required)
os.environ.setdefault("WS_AUTH_DISABLED", "true")
# Disable PII hashing in tests so existing tests asserting raw values in details continue to pass
os.environ.setdefault("PII_HASH_ENABLED", "false")
# Disable OTLP export in CI — avoids hanging on Railway internal host resolution
os.environ.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)


@pytest.fixture
def admin_headers():
    """Auth headers for admin user (x-user-email + x-user-role)."""
    return {"x-user-email": "admin@example.com", "x-user-role": "admin"}