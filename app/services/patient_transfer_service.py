import uuid

from datetime import datetime

from fastapi import HTTPException

from app.models.patient_therapist import PatientTherapist

from app.repositories.patient_repository import (
    get_patient_by_code
)

from app.repositories.patient_therapist_repository import (
    get_active_assignment
)


def transfer_patient(
    db,
    patient_code: str,
    new_therapist_id: int
):

    patient = get_patient_by_code(
        db,
        patient_code
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Invalid patient code"
        )

    current_assignment = get_active_assignment(
        db,
        patient.id
    )

    if current_assignment:
        current_assignment.is_active = False
        current_assignment.ended_at = datetime.utcnow()

    new_assignment = PatientTherapist(
        patient_id=patient.id,
        therapist_id=new_therapist_id,
        is_active=True
    )

    db.add(new_assignment)

    patient.patient_code = (
        "PAT-" +
        str(uuid.uuid4())[:8].upper()
    )

    db.commit()

    return {
        "message": "Patient transferred successfully",
        "new_patient_code": patient.patient_code
    }
