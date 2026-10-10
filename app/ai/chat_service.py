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
	ChatPeriod,
	ChatPeriodAnalyzed,
	ChatRequest,
	ChatResponse,
	ChatSourceReference,
	ChatSourcesUsed,
)


def _build_response_metadata(
	contexts: list[SqlPatientContext],
	request: ChatRequest,
	notes_by_period: list[list[dict]],
	additional_limitations: list[str],
	semantic_search_available: bool,
	) -> tuple[
		ChatPeriodAnalyzed,
		ChatPeriodAnalyzed | None,
		ChatSourcesUsed,
		list[ChatSourceReference],
		list[str],
	]:
	used_references = [
		reference
		for context in contexts
		for reference in context.source_references
		if reference["source_type"] != "consultation_note"
	]
	used_references.extend(
		{
			"source_type": "consultation_note",
			"source_id": note["note_id"],
			"source_date": note["consultation_date"],
		}
		for notes in notes_by_period
		for note in notes
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
	limitations = [
		limitation
		for context in contexts
		for limitation in context.limitations
	]
	limitations.extend(additional_limitations)
	available_note_count = sum(
		context.sources_used.consultation_notes for context in contexts
	)
	rag_notes = [note for notes in notes_by_period for note in notes]
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
	def analyzed_period(
		context: SqlPatientContext,
		notes: list[dict],
		requested: ChatPeriod | None,
	) -> ChatPeriodAnalyzed:
		observed_dates = [
			reference["source_date"]
			for reference in context.source_references
			if reference["source_type"] != "consultation_note"
		]
		observed_dates.extend(note["consultation_date"] for note in notes)
		if not observed_dates:
			limitations.append(
				"Aucune période observée n'a pu être établie à partir des sources utilisées."
			)
		return ChatPeriodAnalyzed(
			requested_start_date=requested.start_date if requested else None,
			requested_end_date=requested.end_date if requested else None,
			observed_start_date=min(observed_dates) if observed_dates else None,
			observed_end_date=max(observed_dates) if observed_dates else None,
		)

	primary_period = analyzed_period(
		contexts[0],
		notes_by_period[0],
		request.period,
	)
	comparison_period = None
	if request.comparison_period is not None:
		comparison_period = analyzed_period(
			contexts[1],
			notes_by_period[1],
			request.comparison_period,
		)
	unique_references = {
		(reference.source_type, reference.source_id): reference
		for reference in (
			ChatSourceReference.model_validate(item)
			for item in sorted_references
		)
	}
	return (
		primary_period,
		comparison_period,
		ChatSourcesUsed(
			consultations=len({ref.source_id for ref in unique_references.values() if ref.source_type == "consultation"}),
			consultation_notes=len({note["note_id"] for note in rag_notes}),
			sessions=len({ref.source_id for ref in unique_references.values() if ref.source_type == "session"}),
			sessions_with_metrics=len({
				session["session_id"]
				for context in contexts
				for session in context.sessions
				if session["metrics"]
			}),
			session_events=len({ref.source_id for ref in unique_references.values() if ref.source_type == "session_event"}),
		),
		sorted(unique_references.values(), key=lambda ref: (ref.source_date, ref.source_type, ref.source_id)),
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
	contexts = [context]
	periods = [request.period]
	if request.comparison_period is not None:
		contexts.append(
			build_sql_patient_context(
				db,
				request.patient_id,
				therapist_id,
				request.comparison_period,
			)
		)
		periods.append(request.comparison_period)
	additional_limitations = []
	semantic_search_available = bool(
		settings.AI_EMBEDDING_MODEL and is_vector_store_available(db)
	)
	notes_by_period: list[list[dict]] = [[] for _ in contexts]
	if semantic_search_available:
		try:
			for index, period in enumerate(periods):
				if contexts[index].sources_used.consultation_notes:
					notes_by_period[index] = retrieve_consultation_notes(
						db,
						request.patient_id,
						therapist_id,
						request.question,
						period,
					)
		except (LLMProviderError, SQLAlchemyError):
			db.rollback()
			semantic_search_available = False
	if not semantic_search_available:
		for index, period in enumerate(periods):
			notes_by_period[index] = retrieve_consultation_notes_sql(
				db,
				request.patient_id,
				therapist_id,
				period,
				settings.AI_SQL_FALLBACK_NOTE_LIMIT,
			)
		additional_limitations.append(
			"La recherche sémantique sur les notes n'est pas disponible."
		)

	(
		period,
		comparison_period,
		sources_used,
		sources,
		limitations,
	) = _build_response_metadata(
		contexts,
		request,
		notes_by_period,
		additional_limitations,
		semantic_search_available,
	)
	rag_notes = [note for notes in notes_by_period for note in notes]
	has_evidence = bool(
		any(context.consultations or context.sessions or context.session_events for context in contexts)
		or rag_notes
	)
	analysis = None
	if has_evidence:
		try:
			system_prompt, user_prompt = build_chat_prompts(
				request.question,
				context,
				notes_by_period[0],
				contexts[1] if len(contexts) > 1 else None,
				notes_by_period[1] if len(contexts) > 1 else (),
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
		comparison_period_analyzed=comparison_period,
		sources_used=sources_used,
		sources=sources,
		analysis=analysis,
		limitations=list(dict.fromkeys(limitations)),
	)
