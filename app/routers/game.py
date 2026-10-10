from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.game_schema import (
    GameCreate,
    GameResponse,
)

from app.services.game_service import (
    create_game,
    get_games
)

from app.services.auth_service import (
    get_current_therapist
)
from app.models.user import User


def _specialty(db: Session, current_user: dict) -> str:
    """Spécialité lue en base (fiable même avec un jeton émis avant l'ajout des spécialités)."""
    user = db.query(User).filter(User.id == current_user.get("user_id")).first()
    return (user.specialty if user else None) or current_user.get("specialty") or "kinesitherapist"

router = APIRouter(
    prefix="/games",
    tags=["Games"]
)


@router.post(
    "/",
    response_model=GameResponse,
    summary="Créer un jeu",
    description="Ajoute un jeu au catalogue.",
    response_description="Le jeu créé.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}},
)
def create_new_game(
    request: GameCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_therapist)
):
    return create_game(
        db,
        request,
        _specialty(db, current_user),
    )


@router.get(
    "/",
    response_model=list[GameResponse],
    summary="Lister les jeux",
    description="Retourne les jeux disponibles dans le catalogue.",
    response_description="La liste des jeux.",
    responses={401: {"description": "Authentification requise ou jeton invalide."}},
)
def get_all_games_route(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_therapist)
):
    return get_games(db, _specialty(db, current_user))