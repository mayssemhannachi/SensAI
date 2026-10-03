from sqlalchemy.orm import Session

from app.models.patient_game import PatientGame


def save_patient_game(
    db: Session,
    patient_game: PatientGame
):
    db.add(patient_game)
    db.commit()
    db.refresh(patient_game)

    return patient_game


def get_patient_games(
    db: Session,
    patient_id: int
):
    return (
        db.query(PatientGame)
        .filter(
            PatientGame.patient_id == patient_id
        )
        .all()
    )