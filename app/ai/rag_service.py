from sqlalchemy.orm import Session

from app.ai.llm_provider import embed_texts
from app.ai.sql_context_service import ensure_current_patient_owner
from app.ai.vector_store_service import (
	index_patient_consultation_notes,
	search_patient_note_vectors,
)
from app.core.config import settings
from app.schemas.chat_schema import ChatPeriod


def retrieve_consultation_notes(
	db: Session,
	patient_id: int,
	therapist_id: int,
	question: str,
	period: ChatPeriod | None = None,
) -> list[dict]:
	ensure_current_patient_owner(db, patient_id, therapist_id)
	if not settings.AI_EMBEDDING_MODEL:
		return []

	indexed_note_count = index_patient_consultation_notes(
		db,
		patient_id,
		therapist_id,
		period,
		settings.AI_EMBEDDING_MODEL,
		embed_texts,
	)
	if indexed_note_count == 0:
		return []

	query_embedding = embed_texts([question])[0]
	return search_patient_note_vectors(
		db,
		patient_id,
		therapist_id,
		query_embedding,
		period,
		settings.AI_EMBEDDING_MODEL,
		settings.AI_RAG_TOP_K,
	)