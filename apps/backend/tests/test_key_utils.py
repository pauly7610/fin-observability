"""Tests for auto-generated key utility."""

import os
import pytest
from apps.backend.database import SessionLocal
from apps.backend.key_utils import get_or_generate_key, _generate_key
from apps.backend.models import SystemConfig


def test_generate_key_format():
    """Generated keys are URL-safe and 32+ chars."""
    k = _generate_key()
    assert len(k) >= 32
    assert all(c.isalnum() or c in "-_" for c in k)


def test_generate_key_no_duplicates():
    """Multiple generations produce unique keys."""
    keys = {_generate_key() for _ in range(100)}
    assert len(keys) == 100


def test_get_or_generate_key_prefers_env(db_session):
    """Env var takes precedence over DB."""
    os.environ["TEST_KEY_ENV"] = "from-env"
    try:
        result = get_or_generate_key(db_session, "test_key_env", "TEST_KEY_ENV")
        assert result == "from-env"
    finally:
        os.environ.pop("TEST_KEY_ENV", None)


def test_get_or_generate_key_persists_and_reuses(db_session):
    """When env unset, generates once and reuses (no dups)."""
    # Use a key we know is not in env
    k1 = get_or_generate_key(db_session, "test_persist_key", "TEST_PERSIST_KEY_NOT_SET")
    k2 = get_or_generate_key(db_session, "test_persist_key", "TEST_PERSIST_KEY_NOT_SET")
    assert k1 == k2
    row = db_session.query(SystemConfig).filter(SystemConfig.key == "test_persist_key").first()
    assert row is not None
    assert row.value == k1


@pytest.fixture
def db_session():
    """Clean DB session for key tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
