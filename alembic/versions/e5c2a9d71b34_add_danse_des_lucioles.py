"""Ajout du jeu « La Danse des Lucioles » (ergothérapie : mémoire et coordination)

Revision ID: e5c2a9d71b34
Revises: a74c98d13e20
Create Date: 2026-10-10

Jeu conçu par Maram (branche maram-game, 9d2341e) : l'enfant reproduit avec ses
mains une séquence de fleurs montrée par Léo (mémoire de travail, planification,
coordination œil-main). Insertion idempotente par slug.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5c2a9d71b34"
down_revision: Union[str, Sequence[str], None] = "a74c98d13e20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NAME = "La Danse des Lucioles"
SLUG = "danse-lucioles"
DESCRIPTION = (
    "Mémoire et coordination : Léo allume des fleurs dans un ordre, l'enfant refait "
    "la même danse en touchant les fleurs avec ses mains."
)


def upgrade() -> None:
    bind = op.get_bind()
    exists = bind.execute(
        sa.text("SELECT 1 FROM games WHERE slug = :slug OR name = :name"),
        {"slug": SLUG, "name": NAME},
    ).first()
    if exists:
        bind.execute(sa.text("UPDATE games SET specialty = 'ergotherapist' WHERE slug = :slug"), {"slug": SLUG})
    else:
        bind.execute(
            sa.text(
                "INSERT INTO games (name, slug, description, specialty) "
                "VALUES (:name, :slug, :description, 'ergotherapist')"
            ),
            {"name": NAME, "slug": SLUG, "description": DESCRIPTION},
        )


def downgrade() -> None:
    bind = op.get_bind()
    used = bind.execute(
        sa.text("SELECT 1 FROM patient_games pg JOIN games g ON g.id = pg.game_id WHERE g.slug = :slug"),
        {"slug": SLUG},
    ).first()
    if not used:
        bind.execute(sa.text("DELETE FROM games WHERE slug = :slug"), {"slug": SLUG})
