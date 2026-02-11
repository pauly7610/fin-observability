from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from .models import User
from .database import get_db
import os

bearer_scheme = HTTPBearer(auto_error=False)
AUTH_MODE = os.getenv("AUTH_MODE", "header")  # "jwt" or "header"


def get_current_user(
    x_user_email: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db=Depends(get_db),
) -> User:
    """
    Retrieve the current user via JWT token (if AUTH_MODE=jwt) or headers (default).
    Supports both modes for backward compatibility during development.
    """
    # Try JWT first if credentials are provided
    if credentials and credentials.credentials:
        from .routers.auth import decode_access_token
        payload = decode_access_token(credentials.credentials)
        if payload:
            email = payload.get("sub")
            user = db.query(User).filter(User.email == email).first()
            if user and user.is_active:
                user.scopes = []
                if hasattr(user, "meta") and user.meta and isinstance(user.meta, dict):
                    user.scopes = user.meta.get("scopes", [])
                return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    # Fall back to header-based auth
    if x_user_email and x_user_role:
        user = db.query(User).filter(User.email == x_user_email).first()
        if user:
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user"
                )
            if user.role != x_user_role:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Role mismatch"
                )
            user.scopes = []
            if hasattr(user, "meta") and user.meta and isinstance(user.meta, dict):
                user.scopes = user.meta.get("scopes", [])
            return user
        # User not in DB — create a transient user object for dev/testing
        virtual_user = User(
            id=0,
            email=x_user_email,
            role=x_user_role,
            full_name=x_user_email.split("@")[0],
            is_active=True,
        )
        virtual_user.scopes = []
        return virtual_user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide JWT Bearer token or x-user-email/x-user-role headers.",
    )


def require_role(roles: List[str], scopes: Optional[List[str]] = None):
    """
    Dependency for RBAC and fine-grained permission scopes.
    Args:
        roles: List of allowed roles (e.g., ["admin", "analyst"]).
        scopes: Optional list of required scopes (e.g., ["ops:execute-agentic"]).
    Raises:
        HTTPException if user lacks role or required scope.
    """

    def dependency(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges (role)",
            )
        if scopes:
            user_scopes = set(getattr(user, "scopes", []) or [])
            required_scopes = set(scopes)
            if not required_scopes.issubset(user_scopes):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient privileges (scope)",
                )
        return user

    return dependency


def require_permission(permission: str):
    """
    Permission-based access control using the RBAC module.
    Checks if the user's role grants the required permission.

    Usage:
        @router.get("/endpoint")
        async def handler(user=Depends(require_permission("model:retrain"))):
            ...
    """
    from .rbac import has_permission, Permission

    def dependency(user: User = Depends(get_current_user)):
        try:
            perm = Permission(permission)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unknown permission: {permission}",
            )
        if not has_permission(user.role, perm):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} not granted to role '{user.role}'",
            )
        return user

    return dependency
