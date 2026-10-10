from fastapi import HTTPException

from app.models.game import Game
from app.models.patient import Patient
from app.models.patient_game import PatientGame
from app.models.user import User

from app.repositories.patient_game_repository import (
    save_patient_game,
    get_patient_games,
)


def assign_game(
    db,
    request,
    therapist_id: int,
):
    patient = db.query(Patient).filter(Patient.id == request.patient_id, Patient.therapist_id == therapist_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    game = db.query(Game).filter(Game.id == request.game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    therapist = db.query(User).filter(User.id == therapist_id).first()
    if not therapist or game.specialty != therapist.specialty:
        raise HTTPException(status_code=403, detail="Game not available in this therapist space")

    patient_game = PatientGame(
        patient_id=request.patient_id,
        game_id=request.game_id,
        configuration=request.configuration,
    )

    return save_patient_game(
        db,
        patient_game,
    )


def get_games_for_patient(
    db,
    patient_id,
    therapist_id: int,
):
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.therapist_id == therapist_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return get_patient_games(
        db,
        patient_id
    )

def update_game_configuration(db, patient_game_id: int, configuration: dict, therapist_id: int):
    patient_game = db.query(PatientGame).filter(PatientGame.id == patient_game_id).first()
    if not patient_game:
        raise HTTPException(status_code=404, detail="Patient game not found")
    if patient_game.patient.therapist_id != therapist_id:
        raise HTTPException(status_code=403, detail="Access denied")
    patient_game.configuration = configuration
    db.commit()
    db.refresh(patient_game)
    return patient_game
