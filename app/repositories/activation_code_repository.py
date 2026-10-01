from sqlalchemy.orm import Session

from app.models.activation_code import ActivationCode


def save_activation_code(
    db: Session,
    activation_code: ActivationCode
):
    db.add(activation_code)
    db.commit()
    db.refresh(activation_code)

    return activation_code
