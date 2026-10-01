from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.patient_schema import PatientCreate, PatientUpdate
from app.services.auth_service import get_current_user
from app.services.patient_service import (
    create_patient,
    get_my_patients,
    get_patient,
    remove_patient,
    update_patient,
)
from app.services.patient_service import (
    create_patient,
    get_my_patients,
    get_patient,
    update_patient,
    remove_patient,
    find_patient_by_code,
    regenerate_patient_code
)

router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
)


@router.post("/")
def create_new_patient(
    request: PatientCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    patient = create_patient(
        db,
        request,
        current_user["user_id"],
    )

    return patient


@router.get("/")
def get_patients(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_my_patients(
        db,
        current_user["user_id"],
    )


@router.get("/{patient_id}")
def get_patient_by_id(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_patient(
        db,
        patient_id,
        current_user["user_id"],
    )


@router.put("/{patient_id}")
def update_patient_route(
    patient_id: int,
    request: PatientUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_patient(
        db,
        patient_id,
        request,
        current_user["user_id"],
    )


@router.delete("/{patient_id}")
def delete_patient_route(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return remove_patient(
        db,
        patient_id,
        current_user["user_id"],
    )

@router.get("/code/{patient_code}")
def get_patient_by_code_route(
    patient_code: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return find_patient_by_code(
        db,
        patient_code
    )

@router.post("/{patient_id}/regenerate-code")
def regenerate_code_route(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return regenerate_patient_code(
        db,
        patient_id,
        current_user["user_id"]
    )
