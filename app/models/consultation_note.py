from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ConsultationNote(Base):
    __tablename__ = "consultation_notes"

    id: Mapped[int] = mapped_column(primary_key=True)

    consultation_id: Mapped[int] = mapped_column(
        ForeignKey("consultations.id"),
        nullable=False,
    )

    therapist_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    note: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    consultation: Mapped["Consultation"] = relationship(
        "Consultation",
        back_populates="notes",
    )