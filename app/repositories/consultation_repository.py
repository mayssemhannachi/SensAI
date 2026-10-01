from sqlalchemy.orm import Session

from app.models.consultation import Consultation


def save_consultation(
    db: Session,
    consultation: Consultation
):
    db.add(consultation)
    db.commit()
    db.refresh(consultation)

    return consultation