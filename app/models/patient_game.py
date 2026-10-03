from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class PatientGame(Base):
    __tablename__ = "patient_games"

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id"),
        nullable=False,
    )

    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.id"),
        nullable=False,
    )

    configuration: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    patient: Mapped["Patient"] = relationship("Patient")
    game: Mapped["Game"] = relationship("Game")
    sessions: Mapped[list["Session"]] = relationship(
    "Session"
)