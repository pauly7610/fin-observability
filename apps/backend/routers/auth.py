from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from ..database import get_db
from ..models import User
from ..security import get_current_user, require_permission
import os

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fin-observability-dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


@router.post("/login", response_model=TokenResponse)
async def login(request: TokenRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    """
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or inactive account",
        )
    if not user.hashed_password or not pwd_context.verify(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    user.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": user.id}
    )
    return TokenResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
        },
    )


@router.post("/register")
async def register(
    email: str,
    password: str,
    full_name: str,
    role: str = "analyst",
    db: Session = Depends(get_db),
):
    """
    Register a new user. Role must be a valid RBAC role.
    """
    from ..rbac import VALID_ROLES

    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{role}'. Must be one of: {sorted(VALID_ROLES)}",
        )
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = pwd_context.hash(password)
    user = User(
        email=email,
        hashed_password=hashed,
        full_name=full_name,
        role=role,
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role}


@router.get("/roles")
async def list_roles():
    """List all roles and their permissions."""
    from ..rbac import get_role_hierarchy

    return get_role_hierarchy()


@router.put("/users/{user_id}/role")
async def assign_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user:role_assign")),
):
    """Admin-only: Assign a role to a user."""
    from ..rbac import VALID_ROLES

    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{role}'. Must be one of: {sorted(VALID_ROLES)}",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    old_role = user.role
    user.role = role
    db.commit()
    return {
        "id": user.id,
        "email": user.email,
        "old_role": old_role,
        "new_role": role,
    }


@router.put("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user:delete")),
):
    """Admin-only: Deactivate a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user.is_active = False
    db.commit()
    return {"id": user.id, "email": user.email, "is_active": False}


@router.get("/me/permissions")
async def my_permissions(
    current_user: User = Depends(get_current_user),
):
    """Get the current user's role and permissions."""
    from ..rbac import get_permissions_for_role

    perms = get_permissions_for_role(current_user.role)
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "permissions": sorted([p.value for p in perms]),
    }
