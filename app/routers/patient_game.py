from fastapi import APIRouter, HTTPException
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.patient_game_schema import (
    PatientGameCreate,
    PatientGameResponse,
)

from app.services.patient_game_service import (
    assign_game,
    get_games_for_patient,
    update_game_configuration,
)
from app.schemas.patient_game_schema import PatientGameUpdate

from app.services.auth_service import (
    get_current_therapist
)

router = APIRouter(
    prefix="/patient-games",
    tags=["Patient Games"]
)
@router.post(
    "/",
    response_model=PatientGameResponse,
    summary="Associer un jeu à un patient",
    description="Crée une configuration de jeu pour un patient accessible au thérapeute authentifié.",
    response_description="L’association patient-jeu créée.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}, 404: {"description": "Patient ou jeu introuvable."}},
)
def assign_game_to_patient(
    request: PatientGameCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_therapist)
):
    try:
        return assign_game(
            db,
            request,
            current_user["user_id"]
        )
    except HTTPException:
        raise
@router.get(
    "/patient/{patient_id}",
    response_model=list[PatientGameResponse],
    summary="Lister les jeux d’un patient",
    description="Retourne les associations de jeux du patient accessible au thérapeute authentifié.",
    response_description="La liste des associations patient-jeu.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}, 404: {"description": "Patient introuvable."}},
)
def get_patient_games_route(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_therapist)
):
    try:
        return get_games_for_patient(
            db,
            patient_id,
            current_user["user_id"]
        )
    except HTTPException:
        raise


@router.put(
    "/{patient_game_id}",
    response_model=PatientGameResponse,
    summary="Modifier les réglages d’un jeu assigné",
    description="Remplace la configuration (angle cible, maintien, vitesse, difficulté…) d’un jeu assigné à un patient du thérapeute.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}, 403: {"description": "Accès refusé."}, 404: {"description": "Association introuvable."}},
)
def update_patient_game_route(
    patient_game_id: int,
    request: PatientGameUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_therapist)
):
    return update_game_configuration(db, patient_game_id, request.configuration, current_user["user_id"])
