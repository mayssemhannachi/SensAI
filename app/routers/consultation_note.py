from fastapi import APIRouter, HTTPException
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.consultation_note_schema import (
    ConsultationNoteCreate,
    ConsultationNoteResponse,
)

from app.services.consultation_note_service import (
    create_note
)

from app.services.auth_service import (
    get_current_therapist
)

router = APIRouter(
    prefix="/consultation-notes",
    tags=["Consultation Notes"]
)


@router.post(
    "/",
    response_model=ConsultationNoteResponse,
    summary="Ajouter une note de consultation",
    description="Ajoute une note à une consultation accessible au thérapeute authentifié.",
    response_description="La note créée.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}, 403: {"description": "Accès refusé."}, 404: {"description": "Consultation introuvable."}},
)
def add_note(
    request: ConsultationNoteCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_therapist)
):
    try:
        return create_note(
            db,
            request,
            current_user["user_id"]
        )
    except HTTPException:
        raise