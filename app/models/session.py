from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy import DateTime
from sqlalchemy import Integer

from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    patient_game_id: Mapped[int] = mapped_column(
        ForeignKey("patient_games.id"),
        nullable=False
    )

    duration_sec: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    metrics: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    patient_game: Mapped["PatientGame"] = relationship(
        "PatientGame"
    )

    events: Mapped[list["SessionEvent"]] = relationship(
    "SessionEvent"
)