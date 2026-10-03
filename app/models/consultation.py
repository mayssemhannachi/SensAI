from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id"),
        nullable=False,
    )

    therapist_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    consultation_date: Mapped[date] = mapped_column(Date, nullable=False)

    diagnosis: Mapped[str | None] = mapped_column(String(255), nullable=True)

    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="consultations",
    )

    therapist: Mapped["User"] = relationship(
        "User",
        back_populates="consultations",
    )

    notes: Mapped[list["ConsultationNote"]] = relationship(
        "ConsultationNote",
        back_populates="consultation",
    )