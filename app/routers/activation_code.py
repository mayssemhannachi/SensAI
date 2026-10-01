from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.activation_code_schema import (
    ActivationCodeCreate
)

from app.services.activation_code_service import (
    create_activation_code
)

from app.services.auth_service import (
    get_current_user
)

router = APIRouter(
    prefix="/activation-codes",
    tags=["Activation Codes"]
)


@router.post("/")
def generate_code(
    request: ActivationCodeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return create_activation_code(
        db,
        request.patient_id,
        current_user["user_id"]
    )
