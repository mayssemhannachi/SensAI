from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.chat_service import answer_chat
from app.database.database import get_db
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.auth_service import get_current_therapist


router = APIRouter(tags=["AI Chat"])


@router.post(
	"/chat",
	response_model=ChatResponse,
	summary="Analyser les données d'un patient",
	description=(
		"Produit une analyse descriptive à partir du contexte SQL et des notes "
		"de consultation autorisées. Les périodes comparées, sources et limites "
		"sont calculées côté backend."
	),
	responses={
		401: {"description": "Authentification requise ou jeton invalide."},
		403: {"description": "Le thérapeute n'est pas propriétaire du patient."},
		404: {"description": "Patient introuvable."},
		422: {"description": "Corps invalide ou période incohérente."},
		503: {"description": "Le service IA ou le fournisseur configuré est indisponible."},
	},
)
def chat(
	request: ChatRequest,
	db: Session = Depends(get_db),
	current_user: dict = Depends(get_current_therapist),
) -> ChatResponse:
	return answer_chat(db, request, current_user["user_id"])