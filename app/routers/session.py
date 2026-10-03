from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.session_schema import SessionCreate, SessionResponse

from app.services.session_service import (
    create_session,
    get_patient_game_sessions
)

from app.services.auth_service import (
    get_current_user
)

router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"]
)


@router.post(
    "/",
    response_model=SessionResponse,
    summary="Créer une session de jeu",
    description="Enregistre une session pour une association patient-jeu accessible au thérapeute authentifié.",
    response_description="La session créée.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}, 403: {"description": "Accès refusé."}, 404: {"description": "Association patient-jeu introuvable."}},
)
def create_new_session(
    request: SessionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        return create_session(
            db,
            request,
            current_user["user_id"]
        )
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=403 if isinstance(exc, PermissionError) else 404, detail=str(exc))


@router.get(
    "/patient-game/{patient_game_id}",
    response_model=list[SessionResponse],
    summary="Lister les sessions d’un jeu patient",
    description="Retourne les sessions d’une association patient-jeu accessible au thérapeute authentifié.",
    response_description="La liste des sessions.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}, 403: {"description": "Accès refusé."}, 404: {"description": "Association patient-jeu introuvable."}},
)
def get_sessions(
    patient_game_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        return get_patient_game_sessions(
            db,
            patient_game_id,
            current_user["user_id"]
        )
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=403 if isinstance(exc, PermissionError) else 404, detail=str(exc))