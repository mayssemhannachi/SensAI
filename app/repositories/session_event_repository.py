from sqlalchemy.orm import Session

from app.models.session_event import SessionEvent


def save_event(
    db: Session,
    event: SessionEvent
):
    db.add(event)
    db.commit()
    db.refresh(event)

    return event


def get_session_events(
    db: Session,
    session_id: int
):
    return (
        db.query(SessionEvent)
        .filter(
            SessionEvent.session_id == session_id
        )
        .all()
    )