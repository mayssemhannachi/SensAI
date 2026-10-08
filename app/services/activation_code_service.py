import secrets
import uuid

from datetime import datetime
from datetime import timedelta

from fastapi import HTTPException

from app.models.activation_code import ActivationCode
from app.models.patient import Patient

from app.repositories.activation_code_repository import (
    save_activation_code
)


# Alphabet sans caractères ambigus (0/O, 1/I) : code à 6 caractères saisi par l'enfant.
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_activation_code(db) -> str:
    for _ in range(20):
        code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(6))
        if not db.query(ActivationCode).filter(ActivationCode.code == code).first():
            return code
    raise HTTPException(status_code=500, detail="Could not generate a unique code")


def create_activation_code(
    db,
    patient_id,
    therapist_id
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if patient.therapist_id != therapist_id:
        raise HTTPException(status_code=403, detail="Access denied")

    activation_code = ActivationCode(
        patient_id=patient_id,
        created_by=therapist_id,
        code=generate_activation_code(db),
        expires_at=datetime.utcnow() + timedelta(days=30),
    )

    return save_activation_code(
        db,
        activation_code
    )


def activate_patient_account(db, code: str, email: str, password: str) -> str:
    """Consomme un code d'activation et crée le compte patient lié."""
    from app.core.security import create_access_token, hash_password
    from app.models.user import User
    from app.repositories.user_repository import find_by_email

    normalized = (code or "").strip().upper().replace("-", "").replace(" ", "")
    activation = db.query(ActivationCode).filter(ActivationCode.code == normalized).first()
    if not activation:
        raise HTTPException(status_code=404, detail="Activation code not recognized")
    if activation.is_used:
        raise HTTPException(status_code=409, detail="Activation code already used")
    if activation.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Activation code expired")
    if len(password or "") < 6:
        raise HTTPException(status_code=400, detail="Password must contain at least 6 characters")
    if find_by_email(db, email):
        raise HTTPException(status_code=409, detail="Email already used")

    patient = db.query(Patient).filter(Patient.id == activation.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if patient.user_id:
        raise HTTPException(status_code=409, detail="Patient account already activated")

    user = User(
        full_name=f"{patient.first_name} {patient.last_name}",
        email=email,
        password=hash_password(password),
        role="patient",
    )
    db.add(user)
    db.flush()
    patient.user_id = user.id
    activation.is_used = True
    activation.used_at = datetime.utcnow()
    db.commit()
    return create_access_token(
        {"user_id": user.id, "sub": user.email, "role": "patient", "patient_id": patient.id}
    )
