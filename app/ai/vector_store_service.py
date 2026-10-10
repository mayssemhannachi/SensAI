import hashlib
from datetime import datetime, time, timedelta, timezone
from typing import Callable

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.consultation import Consultation
from app.models.consultation_note import ConsultationNote
from app.models.consultation_note_embedding import ConsultationNoteEmbedding
from app.models.patient import Patient
from app.schemas.chat_schema import ChatPeriod


EmbeddingFunction = Callable[[list[str]], list[list[float]]]


def is_vector_store_available(db: Session) -> bool:
	if db.get_bind().dialect.name != "postgresql":
		return False
	try:
		return bool(
			db.execute(
				text(
					"SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') "
					"AND to_regclass('consultation_note_embeddings') IS NOT NULL"
				)
			).scalar()
		)
	except SQLAlchemyError:
		db.rollback()
		return False


def _apply_period(query, period: ChatPeriod | None):
	if period is None:
		return query
	if period.start_date is not None:
		query = query.filter(Consultation.consultation_date >= period.start_date)
	if period.end_date is not None:
		query = query.filter(Consultation.consultation_date <= period.end_date)
	return query


def index_patient_consultation_notes(
	db: Session,
	patient_id: int,
	therapist_id: int,
	period: ChatPeriod | None,
	embedding_model: str,
	embedder: EmbeddingFunction,
) -> int:
	notes_query = (
		db.query(
			ConsultationNote.id.label("note_id"),
			ConsultationNote.note.label("text"),
		)
		.join(Consultation, Consultation.id == ConsultationNote.consultation_id)
			.join(Patient, Patient.id == Consultation.patient_id)
			.filter(
				Consultation.patient_id == patient_id,
				Patient.therapist_id == therapist_id,
			)
	)
	notes = _apply_period(notes_query, period).order_by(ConsultationNote.id).all()
	if not notes:
		return 0

	note_ids = [row.note_id for row in notes]
	existing = (
		db.query(ConsultationNoteEmbedding)
		.filter(ConsultationNoteEmbedding.note_id.in_(note_ids))
		.all()
	)
	existing_by_id = {item.note_id: item for item in existing}
	pending = []
	for row in notes:
		content_hash = hashlib.sha256(row.text.encode("utf-8")).hexdigest()
		stored = existing_by_id.get(row.note_id)
		if (
			stored is None
			or stored.content_hash != content_hash
			or stored.embedding_model != embedding_model
		):
			pending.append((row.note_id, row.text, content_hash))

	batch_size = max(1, settings.AI_RAG_BATCH_SIZE)
	try:
		for batch_start in range(0, len(pending), batch_size):
			batch = pending[batch_start : batch_start + batch_size]
			vectors = embedder([text for _, text, _ in batch])
			if len(vectors) != len(batch) or not vectors:
				raise ValueError("Embedding count does not match note count")
			dimensions = {len(vector) for vector in vectors}
			if len(dimensions) != 1 or 0 in dimensions:
				raise ValueError("Embedding vectors have inconsistent dimensions")
			for (note_id, _, content_hash), vector in zip(batch, vectors):
				db.merge(
					ConsultationNoteEmbedding(
						note_id=note_id,
						content_hash=content_hash,
						embedding_model=embedding_model,
						embedding=vector,
						embedded_at=datetime.now(timezone.utc),
					)
				)
		if pending:
			db.commit()
	except Exception:
		db.rollback()
		raise

	return len(notes)


def search_patient_note_vectors(
	db: Session,
	patient_id: int,
	therapist_id: int,
	query_embedding: list[float],
	period: ChatPeriod | None,
	embedding_model: str,
	limit: int,
) -> list[dict]:
	distance = ConsultationNoteEmbedding.embedding.cosine_distance(
		query_embedding
	).label("distance")
	query = (
		db.query(
			ConsultationNote.id.label("note_id"),
			ConsultationNote.consultation_id,
			ConsultationNote.note.label("text"),
			Consultation.consultation_date,
			distance,
		)
		.join(
			ConsultationNote,
			ConsultationNote.id == ConsultationNoteEmbedding.note_id,
		)
		.join(Consultation, Consultation.id == ConsultationNote.consultation_id)
		.join(Patient, Patient.id == Consultation.patient_id)
		.filter(
			Patient.id == patient_id,
			Patient.therapist_id == therapist_id,
			ConsultationNoteEmbedding.embedding_model == embedding_model,
		)
	)
	rows = (
		_apply_period(query, period)
		.order_by(distance)
		.limit(max(1, limit))
		.all()
	)
	return [
		{
			"note_id": row.note_id,
			"consultation_id": row.consultation_id,
			"consultation_date": row.consultation_date,
			"text": row.text,
		}
		for row in rows
	]