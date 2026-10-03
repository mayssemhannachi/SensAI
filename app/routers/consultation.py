from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.consultation_schema import ConsultationCreate, ConsultationResponse

from app.services.consultation_service import (
    create_consultation
)

from app.services.auth_service import (
    get_current_user
)

router = APIRouter(
    prefix="/consultations",
    tags=["Consultations"]
)


@router.post(
    "",
    response_model=ConsultationResponse,
    summary="Créer une consultation",
    description="Crée une consultation pour un patient accessible au thérapeute authentifié.",
    response_description="La consultation créée.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}, 403: {"description": "Accès refusé."}, 404: {"description": "Patient introuvable."}},
)
@router.post(
    "/",
    response_model=ConsultationResponse,
    summary="Créer une consultation",
    description="Crée une consultation pour un patient accessible au thérapeute authentifié.",
    response_description="La consultation créée.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}, 403: {"description": "Accès refusé."}, 404: {"description": "Patient introuvable."}},
)
def create_new_consultation(
    request: ConsultationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    return create_consultation(
        db,
        request,
        current_user["user_id"]
    )