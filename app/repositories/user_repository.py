from sqlalchemy.orm import Session

from app.models.user import User


def find_by_email(
        db: Session,
        email: str
):
    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


def save_user(
        db: Session,
        user: User
):
    db.add(user)
    db.commit()
    db.refresh(user)

    return user