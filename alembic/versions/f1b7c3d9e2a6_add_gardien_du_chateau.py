"""Ajout du jeu « Le Gardien du Château » (ergothérapie : attention et contrôle des gestes)

Revision ID: f1b7c3d9e2a6
Revises: e5c2a9d71b34
Create Date: 2026-10-10

Jeu conçu par Chahed (branche feature/gardien-du-chateau, 41f4ace) : l'enfant fait
le geste demandé par chaque personnage (fée, étoile, couronne, dragon) et se fige
comme une statue quand l'ogre apparaît (attention, inhibition, latéralité).
Insertion idempotente par slug.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1b7c3d9e2a6"
down_revision: Union[str, Sequence[str], None] = "e5c2a9d71b34"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NAME = "Le Gardien du Château"
SLUG = "gardien-chateau"
DESCRIPTION = (
    "Attention et contrôle des gestes : l'enfant fait le geste de chaque personnage "
    "(bras droit, bras gauche, les deux bras…) et se fige comme une statue devant l'ogre."
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
