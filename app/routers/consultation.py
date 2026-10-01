from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.consultation_schema import (
    ConsultationCreate
)

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


@router.post("")
@router.post("/")
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