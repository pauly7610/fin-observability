"""
Auto-generated authentication keys with persistence.

When env vars (WEBHOOK_API_KEY, MCP_API_KEY) are unset, generates secure random keys,
persists them in system_config, and reuses them. No duplicates: same key returned
for the same config key name on every call.
"""

import os
import secrets
from typing import Optional

from sqlalchemy.orm import Session


def _generate_key() -> str:
    """Generate a cryptographically secure random key (URL-safe, 32 bytes)."""
    return secrets.token_urlsafe(32)


def get_or_generate_key(
    db: Session,
    config_key: str,
    env_var: str,
) -> str:
    """
    Return the configured key from env, or a persisted/generated key.

    Priority: env var > database > generate new and persist.
    Generated keys are stored in system_config and reused (no duplicates).
    """
    # Env takes precedence
    from_env = os.getenv(env_var, "").strip()
    if from_env:
        return from_env

    # Check DB
    from .models import SystemConfig

    row = db.query(SystemConfig).filter(SystemConfig.key == config_key).first()
    if row:
        return row.value

    # Generate new, ensure no collision with existing values
    existing_values = {r.value for r in db.query(SystemConfig).all()}
    for _ in range(10):  # Retry if collision (extremely unlikely)
        candidate = _generate_key()
        if candidate not in existing_values:
            db.add(SystemConfig(key=config_key, value=candidate))
            db.commit()
            return candidate

    raise RuntimeError("Failed to generate unique key for system_config")  # pragma: no cover
