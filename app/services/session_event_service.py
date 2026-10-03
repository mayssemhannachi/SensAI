from app.models.session_event import SessionEvent
from app.models.session import Session

from app.repositories.session_event_repository import (
    save_event,
    get_session_events
)


def create_event(
    db,
    request,
    therapist_id: int
):
    session = db.query(Session).filter(Session.id == request.session_id).first()

    if not session:
        raise ValueError("Session not found")

    if session.patient_game.patient.therapist_id != therapist_id:
        raise PermissionError("Access denied")

    event = SessionEvent(
        session_id=request.session_id,
        timestamp_sec=request.timestamp_sec,
        event_data=request.event_data
    )

    return save_event(
        db,
        event
    )


def get_events(
    db,
    session_id,
    therapist_id: int
):
    session = db.query(Session).filter(Session.id == session_id).first()

    if not session:
        raise ValueError("Session not found")

    if session.patient_game.patient.therapist_id != therapist_id:
        raise PermissionError("Access denied")

    return get_session_events(
        db,
        session_id
    )