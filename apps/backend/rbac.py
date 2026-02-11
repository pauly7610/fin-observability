"""
Role-Based Access Control (RBAC) for the Financial Observability Platform.

Defines roles, permissions, and a permission registry that maps
roles to fine-grained actions. Used by security.py's require_role
and require_permission dependencies.

Roles (hierarchical):
  admin      — Full access: manage users, retrain models, configure system
  compliance — Review compliance logs, approve/reject agent actions, run drift checks
  analyst    — Read-only access to dashboards, logs, and explainability
  viewer     — Read-only access to public dashboards only
"""
from enum import Enum
from typing import Dict, FrozenSet, Set


class Role(str, Enum):
    ADMIN = "admin"
    COMPLIANCE = "compliance"
    ANALYST = "analyst"
    VIEWER = "viewer"


class Permission(str, Enum):
    # User management
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_LIST = "user:list"
    USER_ROLE_ASSIGN = "user:role_assign"

    # Compliance & monitoring
    COMPLIANCE_READ = "compliance:read"
    COMPLIANCE_RESOLVE = "compliance:resolve"
    COMPLIANCE_EXPORT = "compliance:export"

    # Agent actions
    AGENT_READ = "agent:read"
    AGENT_APPROVE = "agent:approve"
    AGENT_REJECT = "agent:reject"
    AGENT_TRIAGE = "agent:triage"

    # Model management
    MODEL_READ = "model:read"
    MODEL_RETRAIN = "model:retrain"
    MODEL_DRIFT_CHECK = "model:drift_check"
    MODEL_CONFIG = "model:config"

    # Transactions & anomalies
    TRANSACTION_READ = "transaction:read"
    TRANSACTION_CREATE = "transaction:create"
    ANOMALY_READ = "anomaly:read"
    ANOMALY_TRAIN = "anomaly:train"

    # System
    SYSTEM_METRICS_READ = "system:metrics_read"
    SYSTEM_CONFIG = "system:config"
    AUDIT_READ = "audit:read"

    # Explainability
    EXPLAIN_READ = "explain:read"
    EXPLAIN_BATCH = "explain:batch"


# Role → Permission mapping
ROLE_PERMISSIONS: Dict[Role, FrozenSet[Permission]] = {
    Role.ADMIN: frozenset(Permission),  # Admin gets everything
    Role.COMPLIANCE: frozenset([
        Permission.COMPLIANCE_READ,
        Permission.COMPLIANCE_RESOLVE,
        Permission.COMPLIANCE_EXPORT,
        Permission.AGENT_READ,
        Permission.AGENT_APPROVE,
        Permission.AGENT_REJECT,
        Permission.AGENT_TRIAGE,
        Permission.MODEL_READ,
        Permission.MODEL_DRIFT_CHECK,
        Permission.TRANSACTION_READ,
        Permission.ANOMALY_READ,
        Permission.SYSTEM_METRICS_READ,
        Permission.AUDIT_READ,
        Permission.EXPLAIN_READ,
        Permission.EXPLAIN_BATCH,
        Permission.USER_LIST,
    ]),
    Role.ANALYST: frozenset([
        Permission.COMPLIANCE_READ,
        Permission.AGENT_READ,
        Permission.MODEL_READ,
        Permission.TRANSACTION_READ,
        Permission.ANOMALY_READ,
        Permission.SYSTEM_METRICS_READ,
        Permission.EXPLAIN_READ,
        Permission.AUDIT_READ,
    ]),
    Role.VIEWER: frozenset([
        Permission.COMPLIANCE_READ,
        Permission.TRANSACTION_READ,
        Permission.SYSTEM_METRICS_READ,
        Permission.MODEL_READ,
    ]),
}

VALID_ROLES: Set[str] = {r.value for r in Role}


def get_permissions_for_role(role: str) -> FrozenSet[Permission]:
    """Get all permissions for a given role string."""
    try:
        return ROLE_PERMISSIONS[Role(role)]
    except (ValueError, KeyError):
        return frozenset()


def has_permission(role: str, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    return permission in get_permissions_for_role(role)


def get_role_hierarchy() -> dict:
    """Return role hierarchy with permission counts for API responses."""
    return {
        role.value: {
            "permissions": sorted([p.value for p in perms]),
            "permission_count": len(perms),
        }
        for role, perms in ROLE_PERMISSIONS.items()
    }
