"""Champs de réglage d'un jeu prescrit, propres à chaque jeu.

À appeler à l'intérieur d'un ``st.form`` : la fonction affiche les champs et
renvoie la configuration correspondante (ou lève ``ValueError`` si incohérente
— l'appelant l'affiche après validation du formulaire).
"""

from __future__ import annotations

import streamlit as st

from dashboard.utils.data import CHATEAU_GESTURES, settings_defaults

SPEEDS = {"lente": "Slow", "moderee": "Moderate", "rapide": "Fast"}
DIFFICULTIES = {"faible": "Low", "moyenne": "Medium", "elevee": "High"}
ARMS = {"R": "Right arm", "L": "Left arm", "BI": "Both arms"}
DIRECTIONS = {
    "side": "To the side (abduction)",
    "front": "Forward (flexion)",
    "mid": "Forward, toward the midline",
    "any": "Any direction",
}

GAME_HINTS = {
    "le-hibou": "Cervical rotation: the child turns their head right, then left, and holds the position.",
    "danse-lucioles": "Memory and coordination: Léo lights up flowers in a sequence and the child repeats the same "
                      "dance by touching them with their hands (planning, working memory, eye-hand coordination).",
    "gardien-chateau": "Attention and movement control: standing, the child makes each character's movement "
                       "(fairy, star, crown, dragon) and freezes like a statue when the ogre appears "
                       "(attention, inhibition, right / left laterality).",
    "gardien-lucioles": "Arm elevation (shoulder): the child raises their arm, elbow straight, in the prescribed "
                        "direction and up to the prescribed height.",
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
            return "Choose exactly 3 challenges for Guardian of the Castle."
        return None
    if slug != "gardien-lucioles" and config.get("safety_limit", 0) < config.get("target_angle", 0):
        return "The safety limit must be greater than or equal to the target angle."
    return None


def _hibou_fields(config: dict, key: str) -> dict:
    c1, c2, c3 = st.columns(3)
    with c1:
        target = st.number_input("Target angle (°)", 5, 90, int(config["target_angle"]), step=5,
                                 help="Neck rotation to reach on each side.", key=f"{key}_target")
        safety = st.number_input("Safety limit (°)", 5, 120, int(config["safety_limit"]), step=5,
                                 help="Beyond this, the game asks the child to come back gently.",
                                 key=f"{key}_safety")
    with c2:
        hold = st.number_input("Hold (s)", 1, 15, int(config["hold_seconds"]), key=f"{key}_hold")
        reps = st.number_input("Repetitions", 1, 30, int(config["repetitions"]), key=f"{key}_reps")
    with c3:
        speed = st.selectbox("Speed", list(SPEEDS), format_func=SPEEDS.get,
                             index=_index(SPEEDS, config.get("speed")), key=f"{key}_speed")
        difficulty = st.selectbox("Difficulty", list(DIFFICULTIES), format_func=DIFFICULTIES.get,
                                  index=_index(DIFFICULTIES, config.get("difficulty"), 1),
                                  key=f"{key}_difficulty")
    c4, c6, c5 = st.columns([1, 1, 1.4])
    with c6:
        shoulder = st.number_input("Shoulder threshold (°)", 8, 40, int(config.get("shoulder_threshold", 18)), step=1,
                                   help="Beyond this trunk deviation, the movement counts as a compensation "
                                        "(the child turns their shoulders instead of their neck).",
                                   key=f"{key}_shoulder")
    with c4:
        gain = st.number_input("Camera sensitivity", 0.8, 2.0, float(config.get("camera_gain", 1.25)), step=0.05,
                               help="Amplifies the angle measured by the camera (default 1.25).",
                               key=f"{key}_gain")
    with c5:
        st.write("")
        invert = st.toggle("Invert rotation direction (camera)", value=bool(config.get("invert_direction", False)),
                           help="Turn on if the owl turns the wrong way with this webcam.",
                           key=f"{key}_invert")
    return {**config, "target_angle": int(target), "safety_limit": int(safety),
            "hold_seconds": int(hold), "repetitions": int(reps), "speed": speed,
            "difficulty": difficulty, "camera_gain": round(float(gain), 2), "invert_direction": bool(invert),
            "shoulder_threshold": int(shoulder)}


def _lucioles_fields(config: dict, key: str) -> dict:
    """Mêmes choix que l'écran d'accueil du jeu de Maram (bras, direction, lucioles, hauteur)."""
    c1, c2, c3 = st.columns(3)
    with c1:
        arm = st.selectbox("Arm to train", list(ARMS), format_func=ARMS.get,
                           index=_index(ARMS, config.get("affected_arm")), key=f"{key}_arm",
                           help="One arm: the other must stay at rest (otherwise it counts as compensation). "
                                "Both arms: they must rise together.")
        direction = st.selectbox("How to raise the arm", list(DIRECTIONS), format_func=DIRECTIONS.get,
                                 index=_index(DIRECTIONS, config.get("direction"), 0), key=f"{key}_dir")
    with c2:
        threshold = st.number_input("Arm height (°)", 30, 170, int(config["target_angle"]), step=5,
                                    help="Elevation to reach to attract the fireflies (60 easy, 90 medium, 120 high).",
                                    key=f"{key}_thr")
        reps = st.number_input("Fireflies to bring back", 1, 50, int(config["repetitions"]), key=f"{key}_reps")
    with c3:
        elbow = st.number_input("Min. elbow extension (°)", 90, 180, int(config["elbow_min"]), step=5,
                                help="Below this, the movement is not counted (arm bent).",
                                key=f"{key}_elbow")
        rest = st.number_input("Resting arm tolerance (°)", 10, 60, int(config["rest_tolerance"]), step=5,
                               help="One arm only: if the other arm rises beyond this, it counts as compensation.",
                               key=f"{key}_rest")
    hold = st.number_input("Hold (s)", 0.5, 10.0, float(config["hold_seconds"]), step=0.5, key=f"{key}_hold")
    level = 1 if threshold <= 70 else 2 if threshold <= 110 else 3
    return {**config, "affected_arm": arm, "mode": "bi" if arm == "BI" else "hemi", "direction": direction,
            "target_angle": int(threshold), "elbow_min": int(elbow), "rest_tolerance": int(rest),
            "repetitions": int(reps), "hold_seconds": float(hold),
            "difficulty": ["faible", "moyenne", "elevee"][level - 1]}


HANDS = {"any": "Either hand", "R": "Right hand", "L": "Left hand", "alt": "Both hands, alternating"}
LEVELS = {"easy": "Easy: 2 flowers, numbers shown", "mid": "Medium: 3 flowers, from memory",
          "hard": "Hard: 4 flowers, from memory"}
SIZES = {"big": "Large", "mid": "Medium", "small": "Small"}


def _danse_fields(config: dict, key: str) -> dict:
    """Mêmes choix que l'écran d'accueil de La Danse des Lucioles (Maram)."""
    c1, c2 = st.columns(2)
    with c1:
        hand = st.selectbox("Which hand", list(HANDS), format_func=HANDS.get,
                            index=_index(HANDS, config.get("hand_mode")), key=f"{key}_hand",
                            help="“Both hands, alternating” works on bimanual coordination.")
        level = st.selectbox("Starting level", list(LEVELS), format_func=LEVELS.get,
                             index=_index(LEVELS, config.get("level")), key=f"{key}_level",
                             help="The game then adapts: one more flower after a flawless dance.")
    with c2:
        reps = st.number_input("Number of dances", 1, 30, int(config.get("repetitions", 5)), key=f"{key}_reps")
        size = st.selectbox("Flower size", list(SIZES), format_func=SIZES.get,
                            index=_index(SIZES, config.get("target_size")), key=f"{key}_size",
                            help="The smaller the flowers, the more precise the movement must be.")
    difficulty = {"easy": "faible", "mid": "moyenne", "hard": "elevee"}[level]
    return {**config, "hand_mode": hand, "level": level, "repetitions": int(reps),
            "target_size": size, "difficulty": difficulty}


def _chateau_fields(config: dict, key: str) -> dict:
    """Le Gardien du Château (Chahed) : les 3 défis, le nombre d'essais et la part de l'ogre."""
    current = [g for g in (config.get("gestures") or []) if g in CHATEAU_GESTURES]
    gestures = st.multiselect("The child's 3 challenges", list(CHATEAU_GESTURES), default=current,
                              format_func=CHATEAU_GESTURES.get, max_selections=3, key=f"{key}_gestures",
                              help="Fairies: right / left laterality. Star and crown: coordination. "
                                   "Dragon: crouching down (balance).")
    c1, c2 = st.columns(2)
    with c1:
        trials = st.number_input("Number of trials", 10, 80, int(config.get("trials", 40)), step=5,
                                 key=f"{key}_trials", help="Game length: about 3 seconds per trial.")
    with c2:
        go = st.slider("Share of challenges (%)", 50, 95, int(config.get("go_percent", 80)), step=5, key=f"{key}_go",
                       help="The remaining trials show the ogre: the child must freeze. "
                            "Fewer challenges = more impulse-control practice.")
    difficulty = "faible" if go >= 85 else "moyenne" if go >= 70 else "elevee"
    return {**config, "gestures": list(gestures), "trials": int(trials), "go_percent": int(go),
            "difficulty": difficulty}
