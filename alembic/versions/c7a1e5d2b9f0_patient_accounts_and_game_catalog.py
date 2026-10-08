"""Comptes patients (activation) et catalogue de jeux par défaut

Revision ID: c7a1e5d2b9f0
Revises: 2b741b951998
Create Date: 2026-10-08

- patients.user_id : relie un patient au compte créé lors de l'activation.
- Catalogue de jeux SensAI (insertion idempotente par slug).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c7a1e5d2b9f0"
down_revision: Union[str, Sequence[str], None] = "2b741b951998"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

GAMES = [
    ("Le Hibou", "le-hibou", "Rotation cervicale : l'enfant tourne la tête pour suivre la souris du hibou."),
    ("Color Touch", "color-touch", "Jeu de couleur : toucher les cibles de la bonne couleur."),
    ("Reaction Speed", "reaction-speed", "Jeu de rapidité : réagir vite aux signaux."),
    ("Sequence Memory", "sequence-memory", "Jeu de mémoire : reproduire une séquence de mouvements."),
    ("Tremor Trace", "tremor-trace", "Jeu de précision : suivre un tracé sans trembler."),
    ("Target Tracking", "target-tracking", "Jeu de suivi : suivre une cible du regard et de la tête."),
    ("Balance Builder", "balance-builder", "Jeu d'équilibre : maintenir une posture stable."),
    ("Puzzle Motion", "puzzle-motion", "Jeu de coordination : assembler un puzzle par des mouvements du corps."),
]


def upgrade() -> None:
    op.add_column("patients", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_patients_user_id", "patients", "users", ["user_id"], ["id"])
    op.create_unique_constraint("uq_patients_user_id", "patients", ["user_id"])

    bind = op.get_bind()
    for name, slug, description in GAMES:
        exists = bind.execute(
            sa.text("SELECT 1 FROM games WHERE slug = :slug OR name = :name"),
            {"slug": slug, "name": name},
        ).first()
        if not exists:
            bind.execute(
                sa.text("INSERT INTO games (name, slug, description) VALUES (:name, :slug, :description)"),
                {"name": name, "slug": slug, "description": description},
            )


def downgrade() -> None:
    op.drop_constraint("uq_patients_user_id", "patients", type_="unique")
    op.drop_constraint("fk_patients_user_id", "patients", type_="foreignkey")
    op.drop_column("patients", "user_id")
