from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ConsultationNoteEmbedding(Base):
	__tablename__ = "consultation_note_embeddings"

	note_id: Mapped[int] = mapped_column(
		ForeignKey("consultation_notes.id", ondelete="CASCADE"),
		primary_key=True,
	)
	content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
	embedding_model: Mapped[str] = mapped_column(String(255), nullable=False)
	embedding: Mapped[list[float]] = mapped_column(Vector(), nullable=False)
	embedded_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		default=lambda: datetime.now(timezone.utc),
		nullable=False,
	)