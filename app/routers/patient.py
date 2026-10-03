from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.patient_schema import (
    PatientCreate,
    PatientDeleteResponse,
    PatientResponse,
    PatientUpdate,
)
from app.services.auth_service import get_current_user
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


@router.post(
    "/",
    response_model=PatientResponse,
    summary="Créer un patient",
    description="Crée un patient et l’associe au thérapeute authentifié.",
    response_description="Le patient créé.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}},
)
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


@router.get(
    "/",
    response_model=list[PatientResponse],
    summary="Lister mes patients",
    description="Retourne les patients associés au thérapeute authentifié.",
    response_description="La liste des patients.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}},
)
def get_patients(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_my_patients(
        db,
        current_user["user_id"],
    )


@router.get(
    "/code/{patient_code}",
    response_model=PatientResponse,
    summary="Rechercher un patient par code",
    description="Recherche un patient à partir de son code d’identification.",
    response_description="Le patient correspondant au code.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}, 404: {"description": "Patient introuvable."}},
)
def get_patient_by_code_route(
    patient_code: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return find_patient_by_code(
        db,
        patient_code
    )


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Consulter un patient",
    description="Retourne un patient accessible au thérapeute authentifié.",
    response_description="Le patient demandé.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}, 403: {"description": "Accès refusé."}, 404: {"description": "Patient introuvable."}},
)
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


@router.put(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Modifier un patient",
    description="Met à jour les informations d’un patient accessible au thérapeute authentifié.",
    response_description="Le patient mis à jour.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}, 403: {"description": "Accès refusé."}, 404: {"description": "Patient introuvable."}},
)
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


@router.delete(
    "/{patient_id}",
    response_model=PatientDeleteResponse,
    summary="Supprimer un patient",
    description="Supprime un patient accessible au thérapeute authentifié.",
    response_description="Confirmation de suppression.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}, 403: {"description": "Accès refusé."}, 404: {"description": "Patient introuvable."}},
)
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

@router.post(
    "/{patient_id}/regenerate-code",
    response_model=PatientResponse,
    summary="Régénérer le code patient",
    description="Remplace le code d’identification d’un patient accessible au thérapeute authentifié.",
    response_description="Le patient avec son nouveau code.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}, 403: {"description": "Accès refusé."}, 404: {"description": "Patient introuvable."}},
)
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
