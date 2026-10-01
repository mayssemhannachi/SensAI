from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import (
    find_by_email,
    save_user
)
from app.core.security import hash_password

from app.core.security import (
    verify_password,
    create_access_token
)
from fastapi import Depends, HTTPException

from app.core.security import (
    verify_password,
    create_access_token,
    decode_token
)
def register_user(
        db: Session,
        full_name: str,
        email: str,
        password: str
):

    existing = find_by_email(
        db,
        email
    )

    if existing:
        raise ValueError(
            "Email already exists"
        )

    user = User(
        full_name=full_name,
        email=email,
        password=hash_password(password),
        role="therapist"
    )

    return save_user(
        db,
        user
    )

def login_user(
        db,
        email: str,
        password: str
):

    user = find_by_email(
        db,
        email
    )

    if not user:
        raise ValueError(
            "Invalid credentials"
        )

    if not verify_password(
        password,
        user.password
    ):
        raise ValueError(
            "Invalid credentials"
        )

    token = create_access_token(
        {
            "user_id": user.id,
            "sub": user.email,
            "role": user.role
        }
    )

    return token
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    return payload