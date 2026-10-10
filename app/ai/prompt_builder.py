import json
from dataclasses import asdict
from datetime import date, datetime
from typing import Any, Mapping, Sequence

from app.ai.sql_context_service import SqlPatientContext


SYSTEM_PROMPT = """Tu es un assistant d'analyse destiné exclusivement aux ergothérapeutes.
Rédige uniquement la section d'analyse, en français professionnel et prudent.
Utilise exclusivement le contexte SQL et les notes thérapeutiques fournis.
N'ajoute ni faits, dates, mesures, tendances, causalité ou sources absents du contexte.
Ne pose aucun diagnostic, ne formule aucun pronostic, prescription ou recommandation thérapeutique.
Si les éléments ne permettent pas une conclusion fiable, dis-le clairement dans l'analyse.
Les données structurées proviennent du contexte SQL; les textes libres proviennent uniquement des notes thérapeutiques.
Les dates, sources et limites sont ajoutées par le backend : ne produis pas ces sections."""


def _json_default(value: Any) -> str:
	if isinstance(value, (date, datetime)):
		return value.isoformat()
	raise TypeError(f"Unsupported prompt value: {type(value).__name__}")


def build_chat_prompts(
	question: str,
	sql_context: SqlPatientContext,
	rag_notes: Sequence[Mapping[str, Any]],
) -> tuple[str, str]:
	structured_context = asdict(sql_context)
	structured_context.pop("consultation_notes", None)
	structured_context.pop("source_references", None)
	structured_context.pop("limitations", None)
	structured_context.pop("period_analyzed", None)
	structured_context.pop("sources_used", None)

	user_context = {
		"question": question,
		"sql_data": structured_context,
		"consultation_note_passages": list(rag_notes),
	}
	return SYSTEM_PROMPT, json.dumps(
		user_context,
		ensure_ascii=False,
		default=_json_default,
	)
