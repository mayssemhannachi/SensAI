from sqlalchemy.orm import Session

from app.models.patient_therapist import PatientTherapist


def get_active_assignment(
    db: Session,
    patient_id: int
):
    return (
        db.query(PatientTherapist)
        .filter(
            PatientTherapist.patient_id == patient_id,
            PatientTherapist.is_active == True
        )
        .first()
    )


def save_assignment(
    db: Session,
    assignment: PatientTherapist
):
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment
