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
    get_current_user
)

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
    current_user=Depends(get_current_user)
):
    return create_game(
        db,
        request
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
    current_user=Depends(get_current_user)
):
    return get_games(db)