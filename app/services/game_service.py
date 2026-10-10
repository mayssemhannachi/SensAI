from app.models.game import Game

from app.repositories.game_repository import (
    save_game,
    get_all_games
)


def create_game(
    db,
    request,
    specialty: str = "kinesitherapist",
):
    game = Game(
        name=request.name,
        slug=request.slug,
        description=request.description,
        specialty=specialty,
    )

    return save_game(
        db,
        game
    )


def get_games(db, specialty: str):
    return get_all_games(db, specialty)