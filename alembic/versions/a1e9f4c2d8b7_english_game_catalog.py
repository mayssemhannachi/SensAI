"""Catalogue de jeux en anglais (la plateforme est présentée en anglais)

Revision ID: a1e9f4c2d8b7
Revises: f1b7c3d9e2a6
Create Date: 2026-10-11

Renomme les jeux par leur slug (les slugs, les séances et les réglages ne changent pas).
Le site et le dashboard affichent le nom venant de la base : après cette migration,
tout est en anglais. downgrade() remet les noms français.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1e9f4c2d8b7"
down_revision: Union[str, Sequence[str], None] = "f1b7c3d9e2a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# slug: (nom anglais, description anglaise, nom français, description française)
GAMES = {
    "le-hibou": (
        "The Owl",
        "Neck rotation: the child turns their head to help the owl watch the forest.",
        "Le Hibou",
        "Rotation cervicale : l'enfant tourne la tête pour suivre la souris du hibou.",
    ),
    "gardien-lucioles": (
        "Firefly Guardian",
        "Shoulder elevation: the child raises their arm, elbow straight, to attract the fireflies.",
        "Le Gardien des Lucioles",
        None,
    ),
    "danse-lucioles": (
        "Firefly Dance",
        "Memory and coordination: Léo lights up flowers in an order and the child repeats the dance "
        "by touching them with their hands.",
        "La Danse des Lucioles",
        "Mémoire et coordination : Léo allume des fleurs dans un ordre, l'enfant refait "
        "la même danse en touchant les fleurs avec ses mains.",
    ),
    "gardien-chateau": (
        "Guardian of the Castle",
        "Attention and movement control: the child does the move of each character and freezes "
        "like a statue when the ogre appears.",
        "Le Gardien du Château",
        "Attention et contrôle des gestes : l'enfant fait le geste de chaque personnage "
        "(bras droit, bras gauche, les deux bras…) et se fige comme une statue devant l'ogre.",
    ),
    "color-touch": ("Color Touch", "Color game: touch the targets of the right color.", None,
                    "Jeu de couleur : toucher les cibles de la bonne couleur."),
    "reaction-speed": ("Reaction Speed", "Speed game: react quickly to signals.", None,
                       "Jeu de rapidité : réagir vite aux signaux."),
    "sequence-memory": ("Sequence Memory", "Memory game: repeat a sequence of movements.", None,
                        "Jeu de mémoire : reproduire une séquence de mouvements."),
    "tremor-trace": ("Tremor Trace", "Precision game: follow a path without shaking.", None,
                     "Jeu de précision : suivre un tracé sans trembler."),
    "target-tracking": ("Target Tracking", "Tracking game: follow a target with the eyes and head.", None,
                        "Jeu de suivi : suivre une cible du regard et de la tête."),
    "balance-builder": ("Balance Builder", "Balance game: hold a stable posture.", None,
                        "Jeu d'équilibre : maintenir une posture stable."),
    "puzzle-motion": ("Puzzle Motion", "Coordination game: build a puzzle with body movements.", None,
                      "Jeu de coordination : assembler un puzzle par des mouvements du corps."),
}


def _rename(name_index: int, description_index: int) -> None:
    bind = op.get_bind()
    for slug, values in GAMES.items():
        name, description = values[name_index], values[description_index]
        if name is not None:
            # Un autre jeu porterait déjà ce nom (contrainte d'unicité) : on ne touche pas au nom.
            taken = bind.execute(
                sa.text("SELECT 1 FROM games WHERE name = :name AND slug <> :slug"),
                {"name": name, "slug": slug},
            ).first()
            if not taken:
                bind.execute(sa.text("UPDATE games SET name = :name WHERE slug = :slug"),
                             {"name": name, "slug": slug})
        if description is not None:
            bind.execute(sa.text("UPDATE games SET description = :d WHERE slug = :slug"),
                         {"d": description, "slug": slug})


# Données de démonstration déjà en base (seed) : diagnostics et noms d'exercice en anglais
DEMO_DIAGNOSES = {
    "Torticolis post-traumatique": "Post-traumatic torticollis",
    "Raideur cervicale après immobilisation": "Neck stiffness after immobilization",
    "Cervicalgie posturale": "Postural neck pain",
    "Torticolis musculaire congénital (suivi)": "Congenital muscular torticollis (follow-up)",
    "Rééducation après entorse cervicale": "Rehabilitation after neck sprain",
    "Plagiocéphalie avec limitation de rotation": "Plagiocephaly with limited rotation",
    "Hémiplégie droite (paralysie cérébrale)": "Right hemiplegia (cerebral palsy)",
    "Raideur de l'épaule après fracture de l'humérus": "Shoulder stiffness after humerus fracture",
    "Paralysie obstétricale du plexus brachial": "Obstetric brachial plexus palsy",
    "Trouble développemental de la coordination (dyspraxie)": "Developmental coordination disorder (dyspraxia)",
    "TDAH : difficultés de planification et d'attention": "ADHD: planning and attention difficulties",
    "Hémiplégie cérébrale infantile : coordination des deux mains": "Childhood hemiplegia: two-hand coordination",
    "Retard de développement : autonomie dans les gestes du quotidien": "Developmental delay: independence in daily activities",
    "TDAH : impulsivité et difficultés d'attention": "ADHD: impulsivity and attention difficulties",
    "Trouble de l'attention : fatigabilité en fin d'activité": "Attention disorder: fatigue at the end of activities"
}
EXERCISE_NAMES = {
    "Rotation cervicale": "Neck rotation",
    "Abduction de l'épaule": "Shoulder abduction",
    "Séquence de fleurs (mémoire et coordination)": "Flower sequence (memory and coordination)",
    "Attention et contrôle des gestes (le château)": "Attention and gesture control (the castle)"
}


def _translate_demo_data(mapping_dx: dict, mapping_ex: dict) -> None:
    bind = op.get_bind()
    for old, new in mapping_dx.items():
        bind.execute(sa.text("UPDATE consultations SET diagnosis = :new WHERE diagnosis = :old"),
                     {"new": new, "old": old})
    if bind.dialect.name != "postgresql":
        return
    for old, new in mapping_ex.items():
        bind.execute(
            sa.text("UPDATE sessions SET metrics = jsonb_set(metrics, '{exercise_name}', to_jsonb(CAST(:new AS text))) "
                    "WHERE metrics->>'exercise_name' = :old"),
            {"new": new, "old": old},
        )


def upgrade() -> None:
    _rename(0, 1)
    _translate_demo_data(DEMO_DIAGNOSES, EXERCISE_NAMES)


def downgrade() -> None:
    _rename(2, 3)
    _translate_demo_data({v: k for k, v in DEMO_DIAGNOSES.items()}, {v: k for k, v in EXERCISE_NAMES.items()})
