"""Champs de réglage d'un jeu prescrit, propres à chaque jeu.

À appeler à l'intérieur d'un ``st.form`` : la fonction affiche les champs et
renvoie la configuration correspondante (ou lève ``ValueError`` si incohérente
— l'appelant l'affiche après validation du formulaire).
"""

from __future__ import annotations

import streamlit as st

from dashboard.utils.data import CHATEAU_GESTURES, settings_defaults

SPEEDS = {"lente": "Lente", "moderee": "Modérée", "rapide": "Rapide"}
DIFFICULTIES = {"faible": "Faible", "moyenne": "Moyenne", "elevee": "Élevée"}
ARMS = {"R": "Bras droit", "L": "Bras gauche", "BI": "Les deux bras"}
DIRECTIONS = {
    "side": "Sur le côté (abduction)",
    "front": "Devant (flexion)",
    "mid": "Devant, vers le milieu",
    "any": "Peu importe",
}

GAME_HINTS = {
    "le-hibou": "Rotation cervicale : l’enfant tourne la tête à droite puis à gauche et maintient la position.",
    "danse-lucioles": "Mémoire et coordination : Léo allume des fleurs dans un ordre, l’enfant refait la même "
                      "danse en les touchant avec ses mains (planification, mémoire de travail, œil-main).",
    "gardien-chateau": "Attention et contrôle des gestes : l’enfant, debout, fait le geste de chaque personnage "
                       "(fée, étoile, couronne, dragon) et se fige comme une statue quand l’ogre apparaît "
                       "(attention, inhibition, latéralité droite / gauche).",
    "gardien-lucioles": "Élévation du bras (épaule) : l’enfant lève le bras, coude tendu, dans la direction "
                        "et jusqu’à la hauteur prescrites.",
}


def _index(options: dict, value, default: int = 0) -> int:
    keys = list(options)
    return keys.index(value) if value in keys else default


def settings_fields(slug: str | None, current: dict | None, key: str) -> dict:
    """Affiche les réglages du jeu ``slug`` et renvoie la configuration saisie."""
    config = {**settings_defaults(slug), **(current or {})}
    if slug == "gardien-lucioles":
        return _lucioles_fields(config, key)
    if slug == "danse-lucioles":
        return _danse_fields(config, key)
    if slug == "gardien-chateau":
        return _chateau_fields(config, key)
    return _hibou_fields(config, key)


def validate(slug: str | None, config: dict) -> str | None:
    """Message d'erreur si la configuration est incohérente, sinon ``None``."""
    if slug == "gardien-chateau":
        if len(config.get("gestures") or []) != 3:
            return "Choisissez exactement 3 défis pour Le Gardien du Château."
        return None
    if slug != "gardien-lucioles" and config.get("safety_limit", 0) < config.get("target_angle", 0):
        return "La limite de sécurité doit être supérieure ou égale à l’angle cible."
    return None


def _hibou_fields(config: dict, key: str) -> dict:
    c1, c2, c3 = st.columns(3)
    with c1:
        target = st.number_input("Angle cible (°)", 5, 90, int(config["target_angle"]), step=5,
                                 help="Rotation du cou à atteindre de chaque côté.", key=f"{key}_target")
        safety = st.number_input("Limite de sécurité (°)", 5, 120, int(config["safety_limit"]), step=5,
                                 help="Au-delà, le jeu demande à l’enfant de revenir doucement.",
                                 key=f"{key}_safety")
    with c2:
        hold = st.number_input("Maintien (s)", 1, 15, int(config["hold_seconds"]), key=f"{key}_hold")
        reps = st.number_input("Répétitions", 1, 30, int(config["repetitions"]), key=f"{key}_reps")
    with c3:
        speed = st.selectbox("Vitesse", list(SPEEDS), format_func=SPEEDS.get,
                             index=_index(SPEEDS, config.get("speed")), key=f"{key}_speed")
        difficulty = st.selectbox("Difficulté", list(DIFFICULTIES), format_func=DIFFICULTIES.get,
                                  index=_index(DIFFICULTIES, config.get("difficulty"), 1),
                                  key=f"{key}_difficulty")
    c4, c6, c5 = st.columns([1, 1, 1.4])
    with c6:
        shoulder = st.number_input("Seuil épaules (°)", 8, 40, int(config.get("shoulder_threshold", 18)), step=1,
                                   help="Au-delà de cet écart du buste, le mouvement compte comme une compensation "
                                        "(l'enfant tourne les épaules au lieu du cou).",
                                   key=f"{key}_shoulder")
    with c4:
        gain = st.number_input("Sensibilité caméra", 0.8, 2.0, float(config.get("camera_gain", 1.25)), step=0.05,
                               help="Amplifie l’angle mesuré par la caméra (1,25 par défaut).",
                               key=f"{key}_gain")
    with c5:
        st.write("")
        invert = st.toggle("Inverser le sens de rotation (caméra)", value=bool(config.get("invert_direction", False)),
                           help="À activer si le hibou tourne dans le mauvais sens avec cette webcam.",
                           key=f"{key}_invert")
    return {**config, "target_angle": int(target), "safety_limit": int(safety),
            "hold_seconds": int(hold), "repetitions": int(reps), "speed": speed,
            "difficulty": difficulty, "camera_gain": round(float(gain), 2), "invert_direction": bool(invert),
            "shoulder_threshold": int(shoulder)}


def _lucioles_fields(config: dict, key: str) -> dict:
    """Mêmes choix que l'écran d'accueil du jeu de Maram (bras, direction, lucioles, hauteur)."""
    c1, c2, c3 = st.columns(3)
    with c1:
        arm = st.selectbox("Bras à entraîner", list(ARMS), format_func=ARMS.get,
                           index=_index(ARMS, config.get("affected_arm")), key=f"{key}_arm",
                           help="Un bras : l’autre doit rester au repos (sinon compensation). "
                                "Les deux bras : ils doivent monter ensemble.")
        direction = st.selectbox("Comment lever le bras", list(DIRECTIONS), format_func=DIRECTIONS.get,
                                 index=_index(DIRECTIONS, config.get("direction"), 0), key=f"{key}_dir")
    with c2:
        threshold = st.number_input("Hauteur du bras (°)", 30, 170, int(config["target_angle"]), step=5,
                                    help="Élévation à atteindre pour attirer les lucioles (60 facile, 90 moyen, 120 haut).",
                                    key=f"{key}_thr")
        reps = st.number_input("Lucioles à ramener", 1, 50, int(config["repetitions"]), key=f"{key}_reps")
    with c3:
        elbow = st.number_input("Extension min. du coude (°)", 90, 180, int(config["elbow_min"]), step=5,
                                help="En dessous, le mouvement n’est pas compté (bras plié).",
                                key=f"{key}_elbow")
        rest = st.number_input("Tolérance bras au repos (°)", 10, 60, int(config["rest_tolerance"]), step=5,
                               help="Un seul bras : si l’autre bras monte au-delà, c’est une compensation.",
                               key=f"{key}_rest")
    hold = st.number_input("Maintien (s)", 0.5, 10.0, float(config["hold_seconds"]), step=0.5, key=f"{key}_hold")
    level = 1 if threshold <= 70 else 2 if threshold <= 110 else 3
    return {**config, "affected_arm": arm, "mode": "bi" if arm == "BI" else "hemi", "direction": direction,
            "target_angle": int(threshold), "elbow_min": int(elbow), "rest_tolerance": int(rest),
            "repetitions": int(reps), "hold_seconds": float(hold),
            "difficulty": ["faible", "moyenne", "elevee"][level - 1]}


HANDS = {"any": "Au choix", "R": "Main droite", "L": "Main gauche", "alt": "Les deux à tour de rôle"}
LEVELS = {"easy": "Facile : 2 fleurs, numéros visibles", "mid": "Moyen : 3 fleurs, de mémoire",
          "hard": "Difficile : 4 fleurs, de mémoire"}
SIZES = {"big": "Grandes", "mid": "Moyennes", "small": "Petites"}


def _danse_fields(config: dict, key: str) -> dict:
    """Mêmes choix que l'écran d'accueil de La Danse des Lucioles (Maram)."""
    c1, c2 = st.columns(2)
    with c1:
        hand = st.selectbox("Quelle main", list(HANDS), format_func=HANDS.get,
                            index=_index(HANDS, config.get("hand_mode")), key=f"{key}_hand",
                            help="« Les deux à tour de rôle » travaille la coordination bimanuelle.")
        level = st.selectbox("Niveau de départ", list(LEVELS), format_func=LEVELS.get,
                             index=_index(LEVELS, config.get("level")), key=f"{key}_level",
                             help="Le jeu s’adapte ensuite : une fleur de plus après une danse sans faute.")
    with c2:
        reps = st.number_input("Nombre de danses", 1, 30, int(config.get("repetitions", 5)), key=f"{key}_reps")
        size = st.selectbox("Taille des fleurs", list(SIZES), format_func=SIZES.get,
                            index=_index(SIZES, config.get("target_size")), key=f"{key}_size",
                            help="Plus les fleurs sont petites, plus le geste doit être précis.")
    difficulty = {"easy": "faible", "mid": "moyenne", "hard": "elevee"}[level]
    return {**config, "hand_mode": hand, "level": level, "repetitions": int(reps),
            "target_size": size, "difficulty": difficulty}


def _chateau_fields(config: dict, key: str) -> dict:
    """Le Gardien du Château (Chahed) : les 3 défis, le nombre d'essais et la part de l'ogre."""
    current = [g for g in (config.get("gestures") or []) if g in CHATEAU_GESTURES]
    gestures = st.multiselect("Les 3 défis de l’enfant", list(CHATEAU_GESTURES), default=current,
                              format_func=CHATEAU_GESTURES.get, max_selections=3, key=f"{key}_gestures",
                              help="Fées : latéralité droite / gauche. Étoile et couronne : coordination. "
                                   "Dragon : se baisser (équilibre).")
    c1, c2 = st.columns(2)
    with c1:
        trials = st.number_input("Nombre d’essais", 10, 80, int(config.get("trials", 40)), step=5,
                                 key=f"{key}_trials", help="Durée de la partie : environ 3 secondes par essai.")
    with c2:
        go = st.slider("Part des défis (%)", 50, 95, int(config.get("go_percent", 80)), step=5, key=f"{key}_go",
                       help="Le reste des essais, c’est l’ogre : l’enfant doit se figer. "
                            "Moins de défis = plus de contrôle de l’impulsivité.")
    difficulty = "faible" if go >= 85 else "moyenne" if go >= 70 else "elevee"
    return {**config, "gestures": list(gestures), "trials": int(trials), "go_percent": int(go),
            "difficulty": difficulty}
