from fastapi import APIRouter, HTTPException
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.activation_code_schema import (
    ActivationCodeCreate,
    ActivationCodeResponse,
)

from app.services.activation_code_service import (
    create_activation_code
)

from app.services.auth_service import (
    get_current_therapist
)

router = APIRouter(
    prefix="/activation-codes",
    tags=["Activation Codes"]
)


@router.post(
    "/",
    response_model=ActivationCodeResponse,
    summary="Générer un code d’activation",
    description="Génère un code d’activation pour un patient accessible au thérapeute authentifié.",
    response_description="Le code d’activation généré.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}, 403: {"description": "Accès refusé."}, 404: {"description": "Patient introuvable."}},
)
def generate_code(
    request: ActivationCodeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_therapist)
):
    try:
        return create_activation_code(
            db,
            request.patient_id,
            current_user["user_id"]
        )
    except HTTPException:
        raise
