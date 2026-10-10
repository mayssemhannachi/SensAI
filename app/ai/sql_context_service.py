from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.consultation import Consultation
from app.models.consultation_note import ConsultationNote
from app.models.game import Game
from app.models.patient import Patient
from app.models.patient_game import PatientGame
from app.models.session import Session as GameSession
from app.models.session_event import SessionEvent
from app.schemas.chat_schema import ChatPeriod


@dataclass(frozen=True)
class AnalyzedPeriod:
	requested_start_date: date | None
	requested_end_date: date | None
	observed_start_date: date | None
	observed_end_date: date | None


@dataclass(frozen=True)
class SqlSourcesUsed:
	consultations: int
	consultation_notes: int
	sessions: int
	sessions_with_metrics: int
	session_events: int


@dataclass(frozen=True)
class SqlPatientContext:
	patient: dict[str, Any]
	consultations: list[dict[str, Any]]
	consultation_notes: list[dict[str, Any]]
	sessions: list[dict[str, Any]]
	session_events: list[dict[str, Any]]
	period_analyzed: AnalyzedPeriod
	sources_used: SqlSourcesUsed
	source_references: list[dict[str, Any]]
	limitations: list[str]


def _apply_date_period(query: Any, column: Any, period: ChatPeriod | None) -> Any:
	if period is None:
		return query
	if period.start_date is not None:
		query = query.filter(column >= period.start_date)
	if period.end_date is not None:
		query = query.filter(column <= period.end_date)
	return query


def _apply_datetime_period(
	query: Any,
	column: Any,
	period: ChatPeriod | None,
) -> Any:
	if period is None:
		return query
	if period.start_date is not None:
		query = query.filter(
			column >= datetime.combine(period.start_date, time.min)
		)
	if period.end_date is not None:
		end_exclusive = datetime.combine(
			period.end_date + timedelta(days=1),
			time.min,
		)
		query = query.filter(column < end_exclusive)
	return query


def _row_dict(row: Any) -> dict[str, Any]:
	return dict(row._mapping)


def ensure_current_patient_owner(
	db: Session,
	patient_id: int,
	therapist_id: int,
) -> None:
	patient_owner = (
		db.query(Patient.id, Patient.therapist_id)
		.filter(Patient.id == patient_id)
		.first()
	)
	if patient_owner is None:
		raise HTTPException(status_code=404, detail="Patient not found")
	if patient_owner.therapist_id != therapist_id:
		raise HTTPException(status_code=403, detail="Access denied")


def retrieve_consultation_notes_sql(
	db: Session,
	patient_id: int,
	therapist_id: int,
	period: ChatPeriod | None = None,
	limit: int = 20,
) -> list[dict[str, Any]]:
	ensure_current_patient_owner(db, patient_id, therapist_id)
	query = (
		db.query(
			ConsultationNote.id.label("note_id"),
			ConsultationNote.consultation_id,
			ConsultationNote.note.label("text"),
			Consultation.consultation_date,
		)
		.join(Consultation, Consultation.id == ConsultationNote.consultation_id)
		.join(Patient, Patient.id == Consultation.patient_id)
		.filter(
			Consultation.patient_id == patient_id,
			Patient.therapist_id == therapist_id,
		)
	)
	rows = (
		_apply_date_period(query, Consultation.consultation_date, period)
		.order_by(Consultation.consultation_date.desc(), ConsultationNote.id.desc())
		.limit(max(1, limit))
		.all()
	)
	return [_row_dict(row) for row in rows]


def build_sql_patient_context(
	db: Session,
	patient_id: int,
	therapist_id: int,
	period: ChatPeriod | None = None,
) -> SqlPatientContext:
	ensure_current_patient_owner(db, patient_id, therapist_id)
	patient_row = (
		db.query(Patient.id.label("patient_id"), Patient.age)
		.filter(Patient.id == patient_id)
		.one()
	)

	consultations_query = db.query(
		Consultation.id.label("consultation_id"),
		Consultation.consultation_date,
	).join(Patient, Patient.id == Consultation.patient_id).filter(
		Consultation.patient_id == patient_id,
		Patient.therapist_id == therapist_id,
	)
	consultations = [
		_row_dict(row)
		for row in _apply_date_period(
			consultations_query,
			Consultation.consultation_date,
			period,
		)
		.order_by(Consultation.consultation_date, Consultation.id)
		.all()
	]

	notes_query = (
		db.query(
			ConsultationNote.id.label("note_id"),
			ConsultationNote.consultation_id,
			ConsultationNote.created_at,
			Consultation.consultation_date,
		)
		.join(Consultation, Consultation.id == ConsultationNote.consultation_id)
		.join(Patient, Patient.id == Consultation.patient_id)
		.filter(
			Consultation.patient_id == patient_id,
			Patient.therapist_id == therapist_id,
		)
	)
	consultation_notes = [
		_row_dict(row)
		for row in _apply_date_period(
			notes_query,
			Consultation.consultation_date,
			period,
		)
		.order_by(Consultation.consultation_date, ConsultationNote.id)
		.all()
	]

	sessions_query = (
		db.query(
			GameSession.id.label("session_id"),
			GameSession.patient_game_id,
			GameSession.duration_sec,
			GameSession.metrics,
			GameSession.created_at,
			PatientGame.game_id,
			Game.name.label("game_name"),
		)
		.join(PatientGame, PatientGame.id == GameSession.patient_game_id)
		.join(Game, Game.id == PatientGame.game_id)
		.join(Patient, Patient.id == PatientGame.patient_id)
		.filter(
			PatientGame.patient_id == patient_id,
			Patient.therapist_id == therapist_id,
		)
	)
	session_rows = _apply_datetime_period(
		sessions_query,
		GameSession.created_at,
		period,
	).order_by(GameSession.created_at, GameSession.id).all()
	sessions = []
	session_dates: dict[int, date] = {}
	for row in session_rows:
		session = _row_dict(row)
		session["session_date"] = row.created_at.date()
		sessions.append(session)
		session_dates[row.session_id] = row.created_at.date()

	session_ids = list(session_dates)
	if session_ids:
		event_rows = (
			db.query(
				SessionEvent.id.label("event_id"),
				SessionEvent.session_id,
				SessionEvent.timestamp_sec,
				SessionEvent.event_data,
			)
			.filter(SessionEvent.session_id.in_(session_ids))
			.order_by(SessionEvent.session_id, SessionEvent.timestamp_sec)
			.all()
		)
		session_events = []
		for row in event_rows:
			event = _row_dict(row)
			event["session_date"] = session_dates[row.session_id]
			session_events.append(event)
	else:
		session_events = []

	observed_dates = [
		row["consultation_date"] for row in consultations
	] + [session["session_date"] for session in sessions]
	actual_start = min(observed_dates) if observed_dates else None
	actual_end = max(observed_dates) if observed_dates else None

	limitations = [
		"Les dates indiquent les bornes des sources trouvées et ne garantissent "
		"pas une couverture continue entre elles."
	]
	if not consultations:
		limitations.append("Aucune consultation n'a été trouvée pour cette période.")
	if not consultation_notes:
		limitations.append("Aucune note thérapeutique n'a été trouvée pour cette période.")
	if not sessions:
		limitations.append("Aucune session n'a été trouvée pour cette période.")
	if sessions and not any(session["metrics"] for session in sessions):
		limitations.append("Aucune métrique renseignée n'est disponible dans les sessions.")
	if not session_events:
		limitations.append("Aucun événement de session n'a été trouvé pour cette période.")
	if period is not None and actual_start is not None:
		if period.start_date is not None and actual_start > period.start_date:
			limitations.append(
				"Les enregistrements utilisés commencent le "
				f"{actual_start.isoformat()}, après le début demandé "
				f"({period.start_date.isoformat()})."
			)
		if period.end_date is not None and actual_end < period.end_date:
			limitations.append(
				"Les enregistrements utilisés s'arrêtent le "
				f"{actual_end.isoformat()}, avant la fin demandée "
				f"({period.end_date.isoformat()})."
			)
	if period is not None and not observed_dates:
		limitations.append("Aucune période analysable n'a pu être établie.")

	source_references = []
	source_references.extend(
		{
			"source_type": "consultation",
			"source_id": row["consultation_id"],
			"source_date": row["consultation_date"],
		}
		for row in consultations
	)
	source_references.extend(
		{
			"source_type": "consultation_note",
			"source_id": row["note_id"],
			"source_date": row["consultation_date"],
		}
		for row in consultation_notes
	)
	source_references.extend(
		{
			"source_type": "session",
			"source_id": row["session_id"],
			"source_date": row["session_date"],
		}
		for row in sessions
	)
	source_references.extend(
		{
			"source_type": "session_event",
			"source_id": row["event_id"],
			"source_date": row["session_date"],
		}
		for row in session_events
	)

	return SqlPatientContext(
		patient=_row_dict(patient_row),
		consultations=consultations,
		consultation_notes=consultation_notes,
		sessions=sessions,
		session_events=session_events,
		period_analyzed=AnalyzedPeriod(
			requested_start_date=period.start_date if period else None,
			requested_end_date=period.end_date if period else None,
			observed_start_date=actual_start,
			observed_end_date=actual_end,
		),
		sources_used=SqlSourcesUsed(
			consultations=len(consultations),
			consultation_notes=len(consultation_notes),
			sessions=len(sessions),
			sessions_with_metrics=sum(
				bool(session["metrics"]) for session in sessions
			),
			session_events=len(session_events),
		),
		source_references=source_references,
		limitations=limitations,
	)
