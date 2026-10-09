"""Ajout du jeu « Le Gardien des Lucioles » (abduction de l'épaule)

Revision ID: d3f8b1c4a7e2
Revises: c7a1e5d2b9f0
Create Date: 2026-10-09

Jeu conçu par Maram (branche maram-game), intégré à la plateforme SensAI.
Insertion idempotente par slug.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d3f8b1c4a7e2"
down_revision: Union[str, Sequence[str], None] = "c7a1e5d2b9f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NAME = "Le Gardien des Lucioles"
SLUG = "gardien-lucioles"
DESCRIPTION = (
    "Abduction de l'épaule : l'enfant lève son bras magique, coude tendu, "
    "pour attirer les lucioles dans la lanterne."
)


def upgrade() -> None:
    bind = op.get_bind()
    exists = bind.execute(
        sa.text("SELECT 1 FROM games WHERE slug = :slug OR name = :name"),
        {"slug": SLUG, "name": NAME},
    ).first()
    if not exists:
        bind.execute(
            sa.text("INSERT INTO games (name, slug, description) VALUES (:name, :slug, :description)"),
            {"name": NAME, "slug": SLUG, "description": DESCRIPTION},
        )


def downgrade() -> None:
    bind = op.get_bind()
    used = bind.execute(
        sa.text(
            "SELECT 1 FROM patient_games pg JOIN games g ON g.id = pg.game_id WHERE g.slug = :slug"
        ),
        {"slug": SLUG},
    ).first()
    if not used:
        bind.execute(sa.text("DELETE FROM games WHERE slug = :slug"), {"slug": SLUG})
