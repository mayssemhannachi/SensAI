"""add consultation note embeddings

Revision ID: 8b47d2c3f901
Revises: 7c8d9e0f1a2b
Create Date: 2026-10-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision: str = "8b47d2c3f901"
down_revision: Union[str, Sequence[str], None] = "7c8d9e0f1a2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	op.execute("CREATE EXTENSION IF NOT EXISTS vector")
	op.create_table(
		"consultation_note_embeddings",
		sa.Column(
			"note_id",
			sa.Integer(),
			sa.ForeignKey("consultation_notes.id", ondelete="CASCADE"),
			primary_key=True,
			nullable=False,
		),
		sa.Column("content_hash", sa.String(length=64), nullable=False),
		sa.Column("embedding_model", sa.String(length=255), nullable=False),
		sa.Column("embedding", Vector(), nullable=False),
		sa.Column(
			"embedded_at",
			sa.DateTime(timezone=True),
			server_default=sa.func.now(),
			nullable=False,
		),
	)


def downgrade() -> None:
	op.drop_table("consultation_note_embeddings")