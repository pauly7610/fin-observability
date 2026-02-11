"""
Tests for Role-Based Access Control (RBAC) module.
Verifies role-permission mappings and access control dependencies.
"""
import pytest
from apps.backend.rbac import (
    Role,
    Permission,
    ROLE_PERMISSIONS,
    get_permissions_for_role,
    has_permission,
    VALID_ROLES,
)


class TestRolePermissionMappings:
    def test_admin_has_all_permissions(self):
        """Admin role should have every defined permission."""
        admin_perms = ROLE_PERMISSIONS[Role.ADMIN]
        for perm in Permission:
            assert perm in admin_perms, f"Admin missing permission: {perm.value}"

    def test_admin_permission_count(self):
        """Admin should have exactly as many permissions as are defined."""
        assert len(ROLE_PERMISSIONS[Role.ADMIN]) == len(Permission)

    def test_compliance_cannot_retrain(self):
        """Compliance role should not be able to retrain models."""
        assert not has_permission("compliance", Permission.MODEL_RETRAIN)

    def test_compliance_can_approve(self):
        """Compliance role should be able to approve agent actions."""
        assert has_permission("compliance", Permission.AGENT_APPROVE)

    def test_analyst_read_only(self):
        """Analyst should have read access but not write/approve access."""
        assert has_permission("analyst", Permission.COMPLIANCE_READ)
        assert has_permission("analyst", Permission.TRANSACTION_READ)
        assert not has_permission("analyst", Permission.AGENT_APPROVE)
        assert not has_permission("analyst", Permission.MODEL_RETRAIN)
        assert not has_permission("analyst", Permission.USER_CREATE)

    def test_viewer_minimal_access(self):
        """Viewer should only have read-only access to a few resources."""
        viewer_perms = get_permissions_for_role("viewer")
        assert Permission.COMPLIANCE_READ in viewer_perms
        assert Permission.TRANSACTION_READ in viewer_perms
        assert Permission.MODEL_READ in viewer_perms
        assert Permission.SYSTEM_METRICS_READ in viewer_perms
        # Viewer should NOT have agent, user, or write permissions
        assert Permission.AGENT_APPROVE not in viewer_perms
        assert Permission.USER_CREATE not in viewer_perms
        assert Permission.COMPLIANCE_RESOLVE not in viewer_perms

    def test_unknown_role_returns_empty(self):
        """Unknown role string should return empty permission set."""
        perms = get_permissions_for_role("superadmin")
        assert len(perms) == 0

    def test_valid_roles_set(self):
        """VALID_ROLES should contain all four role values."""
        assert VALID_ROLES == {"admin", "compliance", "analyst", "viewer"}

    def test_has_permission_with_invalid_role(self):
        """has_permission should return False for invalid role."""
        assert not has_permission("nonexistent", Permission.COMPLIANCE_READ)


class TestRequirePermissionDependency:
    """Test the require_permission FastAPI dependency via TestClient."""

    def setup_method(self):
        from apps.backend.main import app
        from fastapi.testclient import TestClient
        self.client = TestClient(app)

    def test_admin_can_access_drift_status(self):
        """Admin should be able to access drift status endpoint."""
        resp = self.client.get(
            "/agent/compliance/drift/status",
            headers={"x-user-email": "admin@finobs.io", "x-user-role": "admin"},
        )
        assert resp.status_code == 200

    def test_viewer_cannot_access_drift_check(self):
        """Viewer should be denied access to drift check (requires model:drift_check)."""
        resp = self.client.post(
            "/agent/compliance/drift/check",
            headers={"x-user-email": "viewer@finobs.io", "x-user-role": "viewer"},
        )
        assert resp.status_code == 403
