from sqlalchemy.orm import Session

from app.models.patient import Patient


def save_patient(
    db: Session,
    patient: Patient
):
    db.add(patient)
    db.commit()
    db.refresh(patient)

    return patient
#Le thérapeute connecté doit voir uniquement ses patients.
def get_patients_by_therapist(
    db,
    therapist_id
):
    return (
        db.query(Patient)
        .filter(
            Patient.therapist_id == therapist_id
        )
        .all()
    )

def get_patient_by_id(
    db: Session,
    patient_id: int
):
    return (
        db.query(Patient)
        .filter(Patient.id == patient_id)
        .first()
    )


def delete_patient(
    db: Session,
    patient: Patient
):
    db.delete(patient)
    db.commit()

def get_patient_by_code(
    db: Session,
    patient_code: str
):
    return (
        db.query(Patient)
        .filter(
            Patient.patient_code == patient_code
        )
        .first()
    )