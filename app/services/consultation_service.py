
from fastapi import HTTPException

from app.models.consultation import Consultation

from app.repositories.consultation_repository import (
    save_consultation
)

from app.repositories.patient_repository import (
    get_patient_by_id
)


def create_consultation(
    db,
    request,
    therapist_id
):
    patient = get_patient_by_id(
        db,
        request.patient_id
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    if patient.therapist_id != therapist_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    consultation = Consultation(
        patient_id=request.patient_id,
        therapist_id=therapist_id,
        consultation_date=request.consultation_date,
        diagnosis=request.diagnosis
    )

    return save_consultation(
        db,
        consultation
    )