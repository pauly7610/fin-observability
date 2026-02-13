"""
PII hashing utilities for reducing personal data exposure risk.

Hashes known PII fields in dicts before storage/logging. Uses deterministic
SHA-256 with a configurable salt for consistent hashing across requests.
"""

import hashlib
import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union

# Salt for deterministic hashing (same input -> same hash for deduplication)
PII_HASH_SALT = os.getenv("PII_HASH_SALT", "fin-observability-pii-salt")
PII_HASH_ENABLED = os.getenv("PII_HASH_ENABLED", "true").lower() == "true"

# Known PII field names (case-insensitive match). Add more as needed.
PII_FIELDS = frozenset(
    {
        "email",
        "email_address",
        "emailaddress",
        "name",
        "full_name",
        "first_name",
        "last_name",
        "given_name",
        "family_name",
        "customer_name",
        "account_holder",
        "address",
        "street_address",
        "street",
        "city",
        "state",
        "postal_code",
        "zip_code",
        "phone",
        "phone_number",
        "mobile",
        "telephone",
        "ssn",
        "social_security",
        "tax_id",
        "passport",
        "driver_license",
        "ip_address",
        "ip",
        "account_number",
        "card_number",
        "routing_number",
        "cvv",
        "cvc",
        "counterparty",
        "counterparty_name",
        "account",
        "sender_account",
        "receiver_account",
        "beneficiary_name",
        "customer_id",
    }
)

# Fields we never hash by value pattern (avoid false positives: amount "50000", id "123", etc.)
# Use normalized forms (lowercase, no punctuation) to match _normalize_key output
PII_ALLOWLIST = frozenset(
    {
        "amount", "id", "transactionid", "confidence", "anomalyscore",
        "status", "action", "decision", "timestamp", "modelversion",
        "currency", "type", "eventtype", "entitytype", "entityid",
        "regulationtags", "parentauditid", "risklevel", "piicount",
    }
)

# Compiled regex patterns for value-based PII detection
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CC_RE = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")  # 16 digits, optional spaces/dashes
_PHONE_RE = re.compile(r"[\+\d][\d\s\-\(\)]{9,}")
_IPV4_RE = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")


def _looks_like_pii(value: str) -> bool:
    """
    Return True if the string value matches known PII patterns (email, SSN, CC, phone, IP).
    Used for value-based detection regardless of field name.
    """
    if not value or not isinstance(value, str) or len(value.strip()) < 5:
        return False
    s = value.strip()
    if _EMAIL_RE.search(s):
        return True
    if _SSN_RE.search(s):
        return True
    if _CC_RE.search(s):
        return True
    if _PHONE_RE.fullmatch(s) or (len(s) >= 10 and _PHONE_RE.search(s)):
        return True
    if _IPV4_RE.search(s):
        return True
    return False


def hash_pii(value: Union[str, bytes], salt: Optional[str] = None) -> str:
    """
    Deterministic hash of a PII value. Same input + salt -> same output.

    Args:
        value: The PII string or bytes to hash.
        salt: Optional salt (defaults to PII_HASH_SALT from env).

    Returns:
        Hex-encoded SHA-256 hash, prefixed with "pii:" to indicate hashed data.
    """
    if value is None:
        return ""
    str_val = value.decode("utf-8") if isinstance(value, bytes) else str(value)
    if str_val.strip().startswith("pii:"):
        return str_val
    s = salt or PII_HASH_SALT
    digest = hashlib.sha256((s + str_val).encode("utf-8")).hexdigest()
    return f"pii:{digest[:32]}"


def _normalize_key(key: str) -> str:
    """Normalize dict key for PII matching (lowercase, underscores)."""
    return re.sub(r"[^a-z0-9]", "", key.lower().replace("-", "_"))


def _is_allowlisted(key: str) -> bool:
    """Check if key is in allowlist (never hash by value pattern)."""
    normalized = _normalize_key(key)
    return normalized in PII_ALLOWLIST


def _should_hash_value(key: str, value: Any, custom_fields: Optional[List[str]] = None) -> bool:
    """Hash if field name matches PII_FIELDS, or (if not allowlisted) value matches PII pattern."""
    if _is_allowlisted(key):
        return False
    if _is_pii_field(key, custom_fields):
        return True
    if isinstance(value, str) and value.strip() and _looks_like_pii(value):
        return True
    return False


def _is_pii_field(key: str, custom_fields: Optional[List[str]] = None) -> bool:
    """Check if a dict key matches a known PII field name."""
    normalized = _normalize_key(key)
    if normalized in PII_FIELDS:
        return True
    if custom_fields:
        for cf in custom_fields:
            if _normalize_key(cf) == normalized or normalized.endswith(_normalize_key(cf)):
                return True
    # Substring match for common patterns (e.g. "customer_email", "billing_address")
    for pii in PII_FIELDS:
        if pii in normalized or normalized.endswith(pii):
            return True
    return False


def _hash_value(val: Any, salt: Optional[str] = None) -> Any:
    """Hash a scalar value if it looks like PII (string)."""
    if isinstance(val, str) and val.strip():
        return hash_pii(val, salt)
    return val


def hash_pii_in_dict(
    obj: Dict[str, Any],
    fields: Optional[List[str]] = None,
    salt: Optional[str] = None,
    enabled: bool = True,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Recursively hash PII fields in a dict. Returns the sanitized dict and risk info.

    Args:
        obj: Dict to process (e.g. transaction meta, compliance log meta).
        fields: Optional list of additional field names to treat as PII.
        salt: Optional salt for hashing.
        enabled: If False, returns obj unchanged (for feature flag).

    Returns:
        (sanitized_dict, risk_info) where risk_info has:
        - fields_hashed: list of field paths that were hashed
        - pii_count: number of values hashed
        - risk_level: "low" | "medium" | "high" based on pii_count
    """
    if not enabled or not PII_HASH_ENABLED:
        return obj, {"fields_hashed": [], "pii_count": 0, "risk_level": "low"}

    s = salt or PII_HASH_SALT
    fields_hashed: List[str] = []
    pii_count = 0

    def _walk(data: Any, path: str = "") -> Any:
        nonlocal pii_count
        if isinstance(data, dict):
            out: Dict[str, Any] = {}
            for k, v in data.items():
                full_path = f"{path}.{k}" if path else k
                if _should_hash_value(k, v, fields):
                    out[k] = _hash_value(v, s)
                    fields_hashed.append(full_path)
                    pii_count += 1
                else:
                    out[k] = _walk(v, full_path)
            return out
        if isinstance(data, list):
            return [_walk(item, f"{path}[]") for item in data]
        return data

    sanitized = _walk(obj)

    # Simple risk level based on count
    if pii_count == 0:
        risk_level = "low"
    elif pii_count <= 2:
        risk_level = "medium"
    else:
        risk_level = "high"

    risk_info = {
        "fields_hashed": fields_hashed,
        "pii_count": pii_count,
        "risk_level": risk_level,
    }
    return sanitized, risk_info


def assess_pii_risk(
    obj: Dict[str, Any],
    fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Assess PII risk without hashing. Returns fields that would be hashed and risk level.

    Useful for logging or API responses to indicate PII exposure risk.
    """
    fields_found: List[str] = []

    def _scan(data: Any, path: str = "") -> None:
        if isinstance(data, dict):
            for k, v in data.items():
                full_path = f"{path}.{k}" if path else k
                if _should_hash_value(k, v, fields) and isinstance(v, str) and v.strip():
                    fields_found.append(full_path)
                else:
                    _scan(v, full_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                _scan(item, f"{path}[{i}]")

    _scan(obj)

    count = len(fields_found)
    risk_level = "low" if count == 0 else "medium" if count <= 2 else "high"

    return {
        "fields_with_pii": fields_found,
        "pii_count": count,
        "risk_level": risk_level,
        "recommendation": "hash_before_storage" if count > 0 else "none",
    }
