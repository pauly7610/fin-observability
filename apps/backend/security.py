from fastapi import Depends, HTTPException, status, Header
from typing import List, Optional
from .models import User
from .database import get_db

def get_current_user(x_user_email: str = Header(...), x_user_role: str = Header(...), db=Depends(get_db)) -> User:
    user = db.query(User).filter(User.email == x_user_email).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or inactive user")
    if user.role != x_user_role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Role mismatch")
    return user

def require_role(roles: List[str]):
    def dependency(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
        return user
    return dependency
