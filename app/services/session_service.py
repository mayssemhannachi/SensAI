from app.models.session import Session
from app.models.patient_game import PatientGame

from app.repositories.session_repository import (
    save_session,
    get_sessions_by_patient_game
)


def create_session(
    db,
    request,
    therapist_id: int
):
    patient_game = db.query(PatientGame).filter(PatientGame.id == request.patient_game_id).first()

    if not patient_game:
        raise ValueError("Patient game not found")

    if patient_game.patient.therapist_id != therapist_id:
        raise PermissionError("Access denied")

    session = Session(
        patient_game_id=request.patient_game_id,
        duration_sec=request.duration_sec,
        metrics=request.metrics
    )

    return save_session(
        db,
        session
    )


def get_patient_game_sessions(
    db,
    patient_game_id,
    therapist_id: int
):
    patient_game = db.query(PatientGame).filter(PatientGame.id == patient_game_id).first()

    if not patient_game:
        raise ValueError("Patient game not found")

    if patient_game.patient.therapist_id != therapist_id:
        raise PermissionError("Access denied")

    return get_sessions_by_patient_game(
        db,
        patient_game_id
    )