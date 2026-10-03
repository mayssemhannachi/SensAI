from sqlalchemy import ForeignKey
from sqlalchemy import Float

from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base


class SessionEvent(Base):
    __tablename__ = "session_events"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id"),
        nullable=False
    )

    timestamp_sec: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    event_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False
    )

    session: Mapped["Session"] = relationship(
        "Session"
    )