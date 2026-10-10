"""Add therapist specialties and separate game catalogs.

Revision ID: a74c98d13e20
Revises: d3f8b1c4a7e2
Create Date: 2026-10-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a74c98d13e20"
down_revision: Union[str, Sequence[str], None] = "d3f8b1c4a7e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ERGOTHERAPY_GAME_SLUGS = (
    "color-touch",
    "reaction-speed",
    "sequence-memory",
    "tremor-trace",
    "target-tracking",
    "balance-builder",
    "puzzle-motion",
)


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "specialty",
            sa.String(length=40),
            server_default="kinesitherapist",
            nullable=False,
        ),
    )
    op.add_column(
        "games",
        sa.Column(
            "specialty",
            sa.String(length=40),
            server_default="kinesitherapist",
            nullable=False,
        ),
    )

    games = op.get_bind()
    games.execute(
        sa.text(
            "UPDATE games SET specialty = 'ergotherapist' "
            "WHERE slug IN :slugs"
        ).bindparams(sa.bindparam("slugs", expanding=True)),
        {"slugs": ERGOTHERAPY_GAME_SLUGS},
    )
    op.alter_column("users", "specialty", server_default=None)
    op.alter_column("games", "specialty", server_default=None)


def downgrade() -> None:
    op.drop_column("games", "specialty")
    op.drop_column("users", "specialty")
