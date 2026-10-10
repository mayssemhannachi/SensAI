from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.ai.llm_provider import LLMProviderError, generate_analysis
from app.ai.prompt_builder import build_chat_prompts
from app.ai.rag_service import retrieve_consultation_notes
from app.ai.sql_context_service import (
	SqlPatientContext,
	build_sql_patient_context,
	retrieve_consultation_notes_sql,
)
from app.ai.vector_store_service import is_vector_store_available
from app.core.config import settings
from app.schemas.chat_schema import (
	ChatPeriodAnalyzed,
	ChatRequest,
	ChatResponse,
	ChatSourceReference,
	ChatSourcesUsed,
)


def _build_response_metadata(
	context: SqlPatientContext,
	request: ChatRequest,
	rag_notes: list[dict],
	additional_limitations: list[str],
	semantic_search_available: bool,
) -> tuple[ChatPeriodAnalyzed, ChatSourcesUsed, list[ChatSourceReference], list[str]]:
	used_references = [
		reference
		for reference in context.source_references
		if reference["source_type"] != "consultation_note"
	]
	used_references.extend(
		{
			"source_type": "consultation_note",
			"source_id": note["note_id"],
			"source_date": note["consultation_date"],
		}
		for note in rag_notes
	)
	unique_references = {
		(reference["source_type"], reference["source_id"]): reference
		for reference in used_references
	}
	sorted_references = sorted(
		unique_references.values(),
		key=lambda reference: (
			reference["source_date"],
			reference["source_type"],
			reference["source_id"],
		),
	)
	observed_dates = [reference["source_date"] for reference in sorted_references]
	observed_start = min(observed_dates) if observed_dates else None
	observed_end = max(observed_dates) if observed_dates else None

	limitations = list(context.limitations)
	limitations.extend(additional_limitations)
	available_note_count = context.sources_used.consultation_notes
	if semantic_search_available and available_note_count and not rag_notes:
		limitations.append(
			"Aucune note thérapeutique pertinente n'a été retrouvée par la recherche sémantique."
		)
	elif semantic_search_available and len(rag_notes) < available_note_count:
		limitations.append(
			f"{len(rag_notes)} note(s) pertinente(s) sur {available_note_count} "
			"note(s) disponibles ont été retenues par la recherche sémantique."
		)
	elif not semantic_search_available and len(rag_notes) < available_note_count:
		limitations.append(
			f"{len(rag_notes)} note(s) récente(s) sur {available_note_count} "
			"note(s) disponibles ont été retenues par la récupération SQL."
		)
	if not observed_dates:
		limitations.append("Aucune période observée n'a pu être établie à partir des sources utilisées.")

	period = request.period
	return (
		ChatPeriodAnalyzed(
			requested_start_date=period.start_date if period else None,
			requested_end_date=period.end_date if period else None,
			observed_start_date=observed_start,
			observed_end_date=observed_end,
		),
		ChatSourcesUsed(
			consultations=context.sources_used.consultations,
			consultation_notes=len(rag_notes),
			sessions=context.sources_used.sessions,
			sessions_with_metrics=context.sources_used.sessions_with_metrics,
			session_events=context.sources_used.session_events,
		),
		[
			ChatSourceReference.model_validate(reference)
			for reference in sorted_references
		],
		list(dict.fromkeys(limitations)),
	)


def answer_chat(
	db: Session,
	request: ChatRequest,
	therapist_id: int,
) -> ChatResponse:
	context = build_sql_patient_context(
		db,
		request.patient_id,
		therapist_id,
		request.period,
	)
	additional_limitations = []
	rag_notes = []
	semantic_search_available = bool(
		settings.AI_EMBEDDING_MODEL and is_vector_store_available(db)
	)
	if semantic_search_available and context.sources_used.consultation_notes:
		try:
			rag_notes = retrieve_consultation_notes(
				db,
				request.patient_id,
				therapist_id,
				request.question,
				request.period,
			)
		except (LLMProviderError, SQLAlchemyError):
			db.rollback()
			semantic_search_available = False
	if not semantic_search_available:
		rag_notes = retrieve_consultation_notes_sql(
			db,
			request.patient_id,
			therapist_id,
			request.period,
			settings.AI_SQL_FALLBACK_NOTE_LIMIT,
		)
		additional_limitations.append(
			"La recherche sémantique sur les notes n'est pas disponible."
		)

	period, sources_used, sources, limitations = _build_response_metadata(
		context,
		request,
		rag_notes,
		additional_limitations,
		semantic_search_available,
	)
	has_evidence = bool(
		context.consultations
		or context.sessions
		or context.session_events
		or rag_notes
	)
	analysis = None
	if has_evidence:
		try:
			system_prompt, user_prompt = build_chat_prompts(
				request.question,
				context,
				rag_notes,
			)
			analysis = generate_analysis(system_prompt, user_prompt)
		except LLMProviderError as error:
			raise HTTPException(
				status_code=503,
				detail="Le service d'analyse IA est indisponible ou mal configuré.",
			) from error
	else:
		limitations.append(
			"Aucune donnée clinique ou session n'est disponible pour produire une analyse fiable."
		)

	return ChatResponse(
		patient_id=request.patient_id,
		conversation_id=request.conversation_id,
		period_analyzed=period,
		sources_used=sources_used,
		sources=sources,
		analysis=analysis,
		limitations=list(dict.fromkeys(limitations)),
	)
