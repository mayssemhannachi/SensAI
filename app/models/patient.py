from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)

    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    age: Mapped[int] = mapped_column(nullable=False)

    patient_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
    )

    therapist_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    # Compte patient créé lors de l'activation (rôle "patient").
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, unique=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    therapist: Mapped["User"] = relationship(
        "User",
        back_populates="patients",
        foreign_keys=[therapist_id],
    )

    consultations: Mapped[list["Consultation"]] = relationship(
        "Consultation",
        back_populates="patient",
    )

    patient_games: Mapped[list["PatientGame"]] = relationship(
        "PatientGame",
    )