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
        password: str,
        specialty: str = "kinesitherapist",
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
        role="therapist",
        specialty=specialty,
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

    claims = {
        "user_id": user.id,
        "sub": user.email,
        "role": user.role
    }
    if user.role == "therapist":
        claims["specialty"] = user.specialty
    if user.role == "patient":
        from app.models.patient import Patient
        patient = db.query(Patient).filter(Patient.user_id == user.id).first()
        if patient:
            claims["patient_id"] = patient.id
    token = create_access_token(claims)

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


def get_current_therapist(current_user=Depends(get_current_user)):
    """Réservé aux comptes thérapeutes (les comptes patients sont refusés)."""
    if current_user.get("role", "therapist") != "therapist":
        raise HTTPException(status_code=403, detail="Therapist account required")
    return current_user


def get_current_patient_user(current_user=Depends(get_current_user)):
    """Réservé aux comptes patients créés par activation."""
    if current_user.get("role") != "patient":
        raise HTTPException(status_code=403, detail="Patient account required")
    return current_user
