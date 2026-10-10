from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    full_name: Mapped[str] = mapped_column(String(150))

    email: Mapped[str] = mapped_column(String(255), unique=True)

    password: Mapped[str] = mapped_column(String(255))

    role: Mapped[str] = mapped_column(String(50))

    specialty: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="kinesitherapist",
    )

    patients: Mapped[list["Patient"]] = relationship(
        "Patient",
        back_populates="therapist",
        foreign_keys="Patient.therapist_id",
    )

    consultations: Mapped[list["Consultation"]] = relationship(
        "Consultation",
        back_populates="therapist",
    )