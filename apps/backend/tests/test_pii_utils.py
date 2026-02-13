"""Tests for PII hashing utilities."""

import pytest
from apps.backend import pii_utils
from apps.backend.pii_utils import (
    hash_pii,
    hash_pii_in_dict,
    assess_pii_risk,
)


def test_hash_pii_deterministic():
    """Same input produces same hash."""
    a = hash_pii("john@example.com")
    b = hash_pii("john@example.com")
    assert a == b
    assert a.startswith("pii:")
    assert len(a) == 36  # "pii:" + 32 hex chars


def test_hash_pii_different_inputs():
    """Different inputs produce different hashes."""
    a = hash_pii("john@example.com")
    b = hash_pii("jane@example.com")
    assert a != b


def test_hash_pii_empty_and_none():
    """Empty and None values handled."""
    assert hash_pii("").startswith("pii:") and len(hash_pii("")) == 36
    assert hash_pii(None) == ""


def test_value_based_pii_detection(monkeypatch):
    """Unknown field names with PII-like values (email, SSN) should be hashed."""
    monkeypatch.setattr(pii_utils, "PII_HASH_ENABLED", True)
    data = {"unknown_field": "john@example.com", "some_id": "123-45-6789"}
    sanitized, risk = hash_pii_in_dict(data)
    assert sanitized["unknown_field"].startswith("pii:")
    assert sanitized["some_id"].startswith("pii:")
    assert risk["pii_count"] == 2


def test_allowlist_prevents_false_positives(monkeypatch):
    """Allowlisted fields (amount, transaction_id) should not be hashed by value pattern."""
    monkeypatch.setattr(pii_utils, "PII_HASH_ENABLED", True)
    data = {"amount": "50000", "transaction_id": "123-45-6789"}
    sanitized, risk = hash_pii_in_dict(data)
    assert sanitized["amount"] == "50000"
    assert sanitized["transaction_id"] == "123-45-6789"
    assert risk["pii_count"] == 0


def test_hash_pii_idempotent():
    """Values already prefixed with pii: are not double-hashed."""
    already_hashed = "pii:abc123def456"
    result = hash_pii(already_hashed)
    assert result == already_hashed


def test_hash_pii_in_dict_hashes_known_fields(monkeypatch):
    """Known PII fields are hashed."""
    monkeypatch.setattr(pii_utils, "PII_HASH_ENABLED", True)
    data = {"email": "user@test.com", "amount": 100, "name": "John Doe"}
    sanitized, risk = hash_pii_in_dict(data)
    assert sanitized["email"].startswith("pii:")
    assert sanitized["name"].startswith("pii:")
    assert sanitized["amount"] == 100
    assert "email" in risk["fields_hashed"]
    assert "name" in risk["fields_hashed"]
    assert risk["pii_count"] == 2
    assert risk["risk_level"] == "medium"


def test_hash_pii_in_dict_nested(monkeypatch):
    """Nested dicts are processed recursively."""
    monkeypatch.setattr(pii_utils, "PII_HASH_ENABLED", True)
    data = {"customer": {"email": "x@y.com", "full_name": "Jane"}}
    sanitized, risk = hash_pii_in_dict(data)
    assert sanitized["customer"]["email"].startswith("pii:")
    assert sanitized["customer"]["full_name"].startswith("pii:")
    assert "customer.email" in risk["fields_hashed"]
    assert "customer.full_name" in risk["fields_hashed"]
    assert risk["pii_count"] == 2


def test_hash_pii_in_dict_preserves_non_pii():
    """Non-PII fields are preserved."""
    data = {"amount": 500, "currency": "USD", "source": "webhook"}
    sanitized, risk = hash_pii_in_dict(data)
    assert sanitized["amount"] == 500
    assert sanitized["currency"] == "USD"
    assert sanitized["source"] == "webhook"
    assert risk["pii_count"] == 0
    assert risk["risk_level"] == "low"


def test_assess_pii_risk_without_hashing():
    """assess_pii_risk returns risk info without modifying data."""
    data = {"email": "secret@test.com", "amount": 99}
    result = assess_pii_risk(data)
    assert "email" in result["fields_with_pii"]
    assert result["pii_count"] == 1
    assert result["risk_level"] in ("low", "medium", "high")
    assert result["recommendation"] == "hash_before_storage"
    assert data["email"] == "secret@test.com"  # unchanged
