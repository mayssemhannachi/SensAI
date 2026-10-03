from fastapi import HTTPException

from app.models.consultation import Consultation
from app.models.consultation_note import ConsultationNote

from app.repositories.consultation_note_repository import (
    save_note
)


def create_note(
    db,
    request,
    therapist_id
):
    consultation = db.query(Consultation).filter(Consultation.id == request.consultation_id).first()

    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    if consultation.therapist_id != therapist_id:
        raise HTTPException(status_code=403, detail="Access denied")

    note = ConsultationNote(
        consultation_id=request.consultation_id,
        therapist_id=therapist_id,
        note=request.note
    )

    return save_note(
        db,
        note
    )