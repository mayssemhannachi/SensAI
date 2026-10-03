from sqlalchemy.orm import Session

from app.models.session import Session as SessionModel


def save_session(
    db: Session,
    session: SessionModel
):
    db.add(session)
    db.commit()
    db.refresh(session)

    return session


def get_sessions_by_patient_game(
    db: Session,
    patient_game_id: int
):
    return (
        db.query(SessionModel)
        .filter(
            SessionModel.patient_game_id == patient_game_id
        )
        .all()
    )