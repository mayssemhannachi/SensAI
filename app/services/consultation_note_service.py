from app.models.consultation_note import ConsultationNote

from app.repositories.consultation_note_repository import (
    save_note
)


def create_note(
    db,
    request,
    therapist_id
):
    note = ConsultationNote(
        consultation_id=request.consultation_id,
        therapist_id=therapist_id,
        note=request.note
    )

    return save_note(
        db,
        note
    )