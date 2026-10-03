import uuid

from datetime import datetime
from datetime import timedelta

from fastapi import HTTPException

from app.models.activation_code import ActivationCode
from app.models.patient import Patient

from app.repositories.activation_code_repository import (
    save_activation_code
)


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
        code="ACT-" + str(uuid.uuid4())[:8].upper(),
        expires_at=datetime.utcnow() + timedelta(days=30),
    )

    return save_activation_code(
        db,
        activation_code
    )