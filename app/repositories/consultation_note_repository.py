from sqlalchemy.orm import Session

from app.models.consultation_note import ConsultationNote


def save_note(
    db: Session,
    note: ConsultationNote
):
    db.add(note)
    db.commit()
    db.refresh(note)

    return note