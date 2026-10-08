from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.patient_transfer_schema import (
    PatientTransferRequest,
    PatientTransferResponse,
)

from app.services.patient_transfer_service import (
    transfer_patient
)

from app.services.auth_service import (
    get_current_therapist
)

router = APIRouter(
    prefix="/patient-transfers",
    tags=["Patient Transfers"]
)


@router.post(
    "/",
    response_model=PatientTransferResponse,
    summary="Transférer un patient",
    description="Transfère un patient identifié par son code vers le thérapeute authentifié.",
    response_description="Confirmation du transfert et nouveau code patient.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}, 404: {"description": "Code patient invalide."}},
)
def transfer(
    request: PatientTransferRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_therapist)
):
    return transfer_patient(
        db,
        request.patient_code,
        current_user["user_id"]
    )
