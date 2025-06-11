from fastapi import Depends, HTTPException, status, Header
from typing import List, Optional
from .models import User
from .database import get_db


def get_current_user(
    x_user_email: str = Header(...), x_user_role: str = Header(...), db=Depends(get_db)
) -> User:
    """
    Retrieve the current user from headers and DB, ensure active and role matches.
    """
    user = db.query(User).filter(User.email == x_user_email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or inactive user"
        )
    if user.role != x_user_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Role mismatch"
        )
    # Attach scopes from meta if present (or add scopes field to User model in future)
    user.scopes = []
    if hasattr(user, "meta") and user.meta and isinstance(user.meta, dict):
        user.scopes = user.meta.get("scopes", [])
    return user


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
