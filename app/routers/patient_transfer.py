from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.patient_transfer_schema import (
    PatientTransferRequest
)

from app.services.patient_transfer_service import (
    transfer_patient
)

from app.services.auth_service import (
    get_current_user
)

router = APIRouter(
    prefix="/patient-transfers",
    tags=["Patient Transfers"]
)


@router.post("/")
def transfer(
    request: PatientTransferRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return transfer_patient(
        db,
        request.patient_code,
        current_user["user_id"]
    )
