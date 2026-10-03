from sqlalchemy.orm import Session

from app.models.game import Game


def save_game(
    db: Session,
    game: Game
):
    db.add(game)
    db.commit()
    db.refresh(game)

    return game


def get_all_games(
    db: Session
):
    return db.query(Game).all()