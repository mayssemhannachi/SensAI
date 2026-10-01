from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.consultation_note_schema import (
    ConsultationNoteCreate
)

from app.services.consultation_note_service import (
    create_note
)

from app.services.auth_service import (
    get_current_user
)

router = APIRouter(
    prefix="/consultation-notes",
    tags=["Consultation Notes"]
)


@router.post("/")
def add_note(
    request: ConsultationNoteCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return create_note(
        db,
        request,
        current_user["user_id"]
    )