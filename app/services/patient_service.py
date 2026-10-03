import uuid

from fastapi import HTTPException

from app.models.patient import Patient
from app.repositories.patient_repository import (
    delete_patient,
    get_patient_by_code,
    get_patient_by_id,
    get_patients_by_therapist,
    save_patient,
)

def generate_patient_code():
    return str(uuid.uuid4())[:8]


def create_patient(
    db,
    request,
    therapist_id
):
    patient = Patient(
        first_name=request.first_name,
        last_name=request.last_name,
        age=request.age,
        patient_code=generate_patient_code(),
        therapist_id=therapist_id
    )

    return save_patient(
        db,
        patient
    )


def get_my_patients(
    db,
    therapist_id
):
    return get_patients_by_therapist(
        db,
        therapist_id
    )


def get_patient(
    db,
    patient_id,
    therapist_id
):
    patient = get_patient_by_id(
        db,
        patient_id
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

    return patient


def update_patient(
    db,
    patient_id,
    request,
    therapist_id
):
    patient = get_patient(
        db,
        patient_id,
        therapist_id
    )

    patient.first_name = request.first_name
    patient.last_name = request.last_name
    patient.age = request.age

    db.commit()
    db.refresh(patient)

    return patient


def remove_patient(
    db,
    patient_id,
    therapist_id
):
    patient = get_patient(
        db,
        patient_id,
        therapist_id
    )

    delete_patient(db, patient)
    return {
        "message": "Patient deleted",
        "patient_id": patient.id,
    }

def find_patient_by_code(
    db,
    patient_code
):
    patient = get_patient_by_code(
        db,
        patient_code
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    return patient

def regenerate_patient_code(
    db,
    patient_id,
    therapist_id
):
    patient = get_patient(
        db,
        patient_id,
        therapist_id
    )

    patient.patient_code = (
        "PAT-" +
        str(uuid.uuid4())[:8].upper()
    )

    db.commit()
    db.refresh(patient)

    return patient
