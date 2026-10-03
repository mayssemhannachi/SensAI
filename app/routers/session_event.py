from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.session_event_schema import (
    SessionEventCreate,
    SessionEventResponse,
)

from app.services.session_event_service import (
    create_event,
    get_events
)

from app.services.auth_service import (
    get_current_user
)

router = APIRouter(
    prefix="/session-events",
    tags=["Session Events"]
)


@router.post(
    "/",
    response_model=SessionEventResponse,
    summary="Ajouter un événement de session",
    description="Enregistre un événement dans une session accessible au thérapeute authentifié.",
    response_description="L’événement créé.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}, 403: {"description": "Accès refusé."}, 404: {"description": "Session introuvable."}},
)
def add_event(
    request: SessionEventCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        return create_event(
            db,
            request,
            current_user["user_id"]
        )
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=403 if isinstance(exc, PermissionError) else 404, detail=str(exc))


@router.get(
    "/session/{session_id}",
    response_model=list[SessionEventResponse],
    summary="Lister les événements d’une session",
    description="Retourne les événements d’une session accessible au thérapeute authentifié.",
    response_description="La liste des événements.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}, 403: {"description": "Accès refusé."}, 404: {"description": "Session introuvable."}},
)
def get_session_events_route(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        return get_events(
            db,
            session_id,
            current_user["user_id"]
        )
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=403 if isinstance(exc, PermissionError) else 404, detail=str(exc))