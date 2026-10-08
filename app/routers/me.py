"""Espace patient : routes utilisées par l'enfant (ou son parent) une fois le compte activé."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.consultation import Consultation
from app.models.patient import Patient
from app.models.patient_game import PatientGame
from app.models.session import Session as SessionModel
from app.models.user import User
from app.schemas.patient_game_schema import PatientGameDetail
from app.services.auth_service import get_current_patient_user

router = APIRouter(prefix="/me", tags=["Patient Space"])


class MyProfile(BaseModel):
    id: int
    first_name: str
    last_name: str
    age: int
    patient_code: str
    therapist_name: str | None = None
    diagnosis: str | None = None


class MySessionCreate(BaseModel):
    patient_game_id: int
    duration_sec: int
    metrics: dict


class MySession(BaseModel):
    id: int
    patient_game_id: int
    game_id: int
    game_name: str | None = None
    game_slug: str | None = None
    duration_sec: int
    metrics: dict
    created_at: datetime


def _my_patient(current_user, db) -> Patient:
    patient = db.query(Patient).filter(Patient.user_id == current_user["user_id"]).first()
    if not patient:
        raise HTTPException(status_code=404, detail="No patient linked to this account")
    return patient


def _detail(pg: PatientGame) -> dict:
    return {
        "id": pg.id,
        "patient_id": pg.patient_id,
        "game_id": pg.game_id,
        "configuration": pg.configuration or {},
        "game_name": pg.game.name if pg.game else None,
        "game_slug": pg.game.slug if pg.game else None,
    }


@router.get("/patient", response_model=MyProfile, summary="Mon profil patient")
def my_profile(current_user=Depends(get_current_patient_user), db: Session = Depends(get_db)):
    patient = _my_patient(current_user, db)
    therapist = db.query(User).filter(User.id == patient.therapist_id).first()
    consultation = (
        db.query(Consultation)
        .filter(Consultation.patient_id == patient.id, Consultation.diagnosis.isnot(None))
        .order_by(Consultation.consultation_date.desc(), Consultation.id.desc())
        .first()
    )
    return {
        "id": patient.id,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "age": patient.age,
        "patient_code": patient.patient_code,
        "therapist_name": therapist.full_name if therapist else None,
        "diagnosis": consultation.diagnosis if consultation else None,
    }


@router.get("/games", response_model=list[PatientGameDetail], summary="Mes jeux et leurs réglages")
def my_games(current_user=Depends(get_current_patient_user), db: Session = Depends(get_db)):
    patient = _my_patient(current_user, db)
    games = db.query(PatientGame).filter(PatientGame.patient_id == patient.id).order_by(PatientGame.id).all()
    return [_detail(pg) for pg in games]


@router.get("/sessions", response_model=list[MySession], summary="Mes séances")
def my_sessions(current_user=Depends(get_current_patient_user), db: Session = Depends(get_db)):
    patient = _my_patient(current_user, db)
    rows = (
        db.query(SessionModel, PatientGame)
        .join(PatientGame, SessionModel.patient_game_id == PatientGame.id)
        .filter(PatientGame.patient_id == patient.id)
        .order_by(SessionModel.created_at.desc())
        .all()
    )
    return [
        {
            "id": s.id,
            "patient_game_id": pg.id,
            "game_id": pg.game_id,
            "game_name": pg.game.name if pg.game else None,
            "game_slug": pg.game.slug if pg.game else None,
            "duration_sec": s.duration_sec,
            "metrics": s.metrics or {},
            "created_at": s.created_at,
        }
        for s, pg in rows
    ]


@router.post("/sessions", response_model=MySession, status_code=201, summary="Enregistrer une séance de jeu")
def create_my_session(
    request: MySessionCreate,
    current_user=Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    patient = _my_patient(current_user, db)
    pg = db.query(PatientGame).filter(PatientGame.id == request.patient_game_id).first()
    if not pg or pg.patient_id != patient.id:
        raise HTTPException(status_code=404, detail="Game not assigned to this patient")
    if (pg.configuration or {}).get("active") is False:
        raise HTTPException(status_code=403, detail="This game is disabled by the therapist")
    session = SessionModel(
        patient_game_id=pg.id,
        duration_sec=max(0, int(request.duration_sec)),
        metrics=request.metrics,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {
        "id": session.id,
        "patient_game_id": pg.id,
        "game_id": pg.game_id,
        "game_name": pg.game.name if pg.game else None,
        "game_slug": pg.game.slug if pg.game else None,
        "duration_sec": session.duration_sec,
        "metrics": session.metrics or {},
        "created_at": session.created_at,
    }
