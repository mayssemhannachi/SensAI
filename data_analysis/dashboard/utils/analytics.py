"""Calculs d'analyse (fonctions pures pandas, sans Streamlit) — testables.

Les seuils cliniques sont regroupés ici pour être ajustés en un seul endroit.
Ce sont des indicateurs d'aide au suivi, pas des critères diagnostiques.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# ==========================================================
# SEUILS
# ==========================================================

LOW_SUCCESS = 40.0          # % de réussite en dessous duquel on alerte
HIGH_PAIN = 4               # douleur déclarée (0-5) à partir de laquelle on alerte
INACTIVE_DAYS = 14          # jours sans séance avant alerte d'assiduité
TREND_WINDOW = 5            # nombre de séances pour la tendance récente
TREND_SIGNIFICANT = 1.0     # points de score par séance (pente)
MIN_SESSIONS_FOR_TREND = 3

SCORE_DROP = 10.0           # baisse du score moyen (3 dernières vs 5 précédentes)
AMPLITUDE_DROP = 3.0        # baisse de l'amplitude moyenne (°)
AMPLITUDE_GAIN = 2.0        # gain d'amplitude moyenne (°) considéré comme une progression
ABDUCTION_DROP = 5.0        # baisse du pic d'abduction moyen (°) — Gardien des Lucioles
ABDUCTION_GAIN = 5.0        # gain du pic d'abduction moyen (°) considéré comme une progression
COMPENSATION_HIGH = 3.0     # compensations par séance (moyenne des 3 dernières) à surveiller
SEQUENCE_GAIN = 1.0         # +1 fleur de séquence moyenne = progression (Danse des Lucioles)
SEQUENCE_ERRORS_HIGH = 4.0  # erreurs d'ordre par séance (moyenne des 3 dernières) à surveiller
INHIBITION_LOW = 60.0       # % de statues réussies (moyenne des 3 dernières) sous lequel l'impulsivité est signalée — Gardien du Château
ATTENTION_FADE = 20.0       # points de réussite perdus entre le début et la fin de la partie (fatigue attentionnelle)
INHIBITION_GAIN = 10.0      # +10 points de statues réussies = progression

STATUS_ORDER = ["Needs attention", "Improving", "Stable", "New"]


def fr(value: float, decimals: int = 1, signed: bool = False) -> str:
    """Number in English format (decimal point)."""
    return f"{value:{'+' if signed else ''}.{decimals}f}"


# ==========================================================
# PÉRIODES
# ==========================================================

PERIODS = {
    "7 days": 7,
    "30 days": 30,
    "90 days": 90,
    "All": None,
}


def period_bounds(sessions: pd.DataFrame, days: int | None,
                  reference: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    end = reference.normalize() + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    if days is None:
        start = sessions["session_date"].min() if not sessions.empty else reference
        return pd.Timestamp(start).normalize(), end
    return reference.normalize() - pd.Timedelta(days=days - 1), end


def filter_period(sessions: pd.DataFrame, days: int | None,
                  reference: pd.Timestamp) -> pd.DataFrame:
    if days is None or sessions.empty:
        return sessions
    start, end = period_bounds(sessions, days, reference)
    mask = sessions["session_date"].between(start, end)
    return sessions[mask]


def previous_period(sessions: pd.DataFrame, days: int | None,
                    reference: pd.Timestamp) -> pd.DataFrame:
    """La période de même durée juste avant (pour les comparaisons)."""
    if days is None or sessions.empty:
        return sessions.iloc[0:0]
    start, _ = period_bounds(sessions, days, reference)
    previous_end = start - pd.Timedelta(microseconds=1)
    previous_start = start - pd.Timedelta(days=days)
    return sessions[sessions["session_date"].between(previous_start, previous_end)]


# ==========================================================
# KPI GLOBAUX
# ==========================================================

def _mean(series: pd.Series) -> float | None:
    value = pd.to_numeric(series, errors="coerce").mean()
    return None if pd.isna(value) else float(value)


def delta(current, previous) -> float | None:
    if current is None or previous is None:
        return None
    return float(current) - float(previous)


def global_kpis(current: pd.DataFrame, previous: pd.DataFrame) -> dict:
    def block(df):
        return {
            "patients": int(df["patient_id"].nunique()),
            "sessions": int(df["session_id"].nunique()) if df["session_id"].notna().any() else len(df),
            "score": _mean(df["score"]),
            "success": _mean(df["success_rate"]),
            "duration": _mean(df["duration_min"]),
        }

    now, before = block(current), block(previous)
    has_previous = not previous.empty
    return {
        key: {
            "value": now[key],
            "delta": delta(now[key], before[key]) if has_previous else None,
        }
        for key in now
    }


# ==========================================================
# TENDANCES
# ==========================================================

def score_slope(scores: pd.Series) -> float | None:
    """Pente (points de score par séance) d'une régression linéaire simple."""
    values = pd.to_numeric(scores, errors="coerce").dropna().to_numpy(dtype=float)
    if len(values) < MIN_SESSIONS_FOR_TREND:
        return None
    x = np.arange(len(values), dtype=float)
    slope = np.polyfit(x, values, 1)[0]
    return float(slope)


def recent_change(values: pd.Series, recent: int = 3, previous: int = 5) -> float | None:
    """Moyenne des ``recent`` dernières valeurs moins celle des ``previous`` d'avant."""
    data = pd.to_numeric(values, errors="coerce").dropna()
    if len(data) < recent + 2:
        return None
    last = data.iloc[-recent:].mean()
    before = data.iloc[-(recent + previous):-recent].mean()
    return float(last - before)


def amplitude_series(history: pd.DataFrame) -> pd.Series:
    """Amplitude moyenne gauche/droite par séance (Le Hibou), vide sinon."""
    if not {"rotation_left", "rotation_right"} <= set(history.columns):
        return pd.Series(dtype=float)
    rot = history[["rotation_left", "rotation_right"]].apply(pd.to_numeric, errors="coerce")
    return rot.mean(axis=1, skipna=False).dropna()


def weekly_trend(sessions: pd.DataFrame) -> pd.DataFrame:
    """Moyennes hebdomadaires (semaines commençant le lundi)."""
    if sessions.empty:
        return pd.DataFrame(columns=["week", "score", "success_rate", "sessions", "patients"])
    df = sessions.dropna(subset=["session_date"]).copy()
    df["week"] = df["session_date"].dt.to_period("W-SUN").dt.start_time
    return (
        df.groupby("week")
        .agg(
            score=("score", "mean"),
            success_rate=("success_rate", "mean"),
            sessions=("patient_id", "size"),
            patients=("patient_id", "nunique"),
        )
        .reset_index()
        .sort_values("week")
    )


def success_distribution(sessions: pd.DataFrame) -> pd.DataFrame:
    bins = [-np.inf, 40, 50, 60, 70, 80, np.inf]
    labels = ["< 40", "40–50", "50–60", "60–70", "70–80", "≥ 80"]
    ranges = pd.cut(sessions["success_rate"], bins=bins, labels=labels, right=False)
    counts = ranges.value_counts().reindex(labels, fill_value=0)
    return pd.DataFrame({"range": labels, "count": counts.to_numpy(dtype=int)})


# ==========================================================
# SYNTHÈSE PAR PATIENT
# ==========================================================

@dataclass
class Alert:
    label: str
    level: str  # "critical" | "warning" | "info"
    detail: str


def abduction_series(history: pd.DataFrame) -> pd.Series:
    """Pic d'abduction moyen par séance (Gardien des Lucioles), vide sinon."""
    if "abduction_mean_peak" not in history.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(history["abduction_mean_peak"], errors="coerce").dropna()


def sequence_series(history: pd.DataFrame) -> pd.Series:
    """Plus longue séquence réussie par séance (Danse des Lucioles), vide sinon."""
    if "max_sequence" not in history.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(history["max_sequence"], errors="coerce").dropna()


def inhibition_series(history: pd.DataFrame) -> pd.Series:
    """% de statues réussies devant l'ogre par séance (Gardien du Château), vide sinon."""
    if "nogo_success_rate" not in history.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(history["nogo_success_rate"], errors="coerce").dropna()


def attention_fade(history: pd.DataFrame) -> pd.Series:
    """Réussite du début moins réussite de la fin de partie, par séance (Gardien du Château)."""
    if not {"accuracy_start", "accuracy_end"} <= set(history.columns):
        return pd.Series(dtype=float)
    start = pd.to_numeric(history["accuracy_start"], errors="coerce")
    end = pd.to_numeric(history["accuracy_end"], errors="coerce")
    return (start - end).dropna()


def patient_alerts(history: pd.DataFrame, reference: pd.Timestamp) -> list[Alert]:
    """Signaux d'attention pour un patient (historique trié par date)."""
    alerts: list[Alert] = []
    if history.empty:
        return alerts
    latest = history.iloc[-1]

    pain = latest.get("pain_level")
    if pain is not None and pd.notna(pain) and pain >= HIGH_PAIN:
        alerts.append(Alert(
            "High pain", "critical",
            f"Reported pain {fr(pain, 0)}/5 at the last session: check range of motion and limit.",
        ))

    success = latest.get("success_rate")
    if pd.notna(success) and success < LOW_SUCCESS:
        alerts.append(Alert(
            "Low success", "critical",
            f"{fr(success, 0)}% success at the last session (threshold {fr(LOW_SUCCESS, 0)}%).",
        ))

    score_drop = recent_change(history["score"])
    if score_drop is not None and score_drop <= -SCORE_DROP:
        alerts.append(Alert(
            "Declining score", "warning",
            f"Average score over the last 3 sessions {fr(score_drop, 0, True)} pts vs previous sessions.",
        ))

    amplitude_drop = recent_change(amplitude_series(history))
    if amplitude_drop is not None and amplitude_drop <= -AMPLITUDE_DROP:
        alerts.append(Alert(
            "Declining range of motion", "warning",
            f"Average rotation {fr(amplitude_drop, 0, True)}° over the last 3 sessions.",
        ))

    abduction_drop = recent_change(abduction_series(history))
    if abduction_drop is not None and abduction_drop <= -ABDUCTION_DROP:
        alerts.append(Alert(
            "Declining abduction", "warning",
            f"Mean abduction peak {fr(abduction_drop, 0, True)}° over the last 3 sessions.",
        ))

    if "compensations" in history.columns:
        comp = pd.to_numeric(history["compensations"], errors="coerce").dropna().tail(3)
        if len(comp) >= 2 and comp.mean() >= COMPENSATION_HIGH:
            alerts.append(Alert(
                "Compensations", "warning",
                f"{fr(comp.mean(), 1)} compensations per session on average (other arm raised or head tilted).",
            ))

    if "sequence_errors" in history.columns:
        errs = pd.to_numeric(history["sequence_errors"], errors="coerce").dropna().tail(3)
        if len(errs) >= 2 and errs.mean() >= SEQUENCE_ERRORS_HIGH:
            alerts.append(Alert(
                "Sequence errors", "warning",
                f"{fr(errs.mean(), 1)} order errors per session on average: level may be too high.",
            ))

    inhibition = inhibition_series(history).tail(3)
    if len(inhibition) >= 2 and inhibition.mean() < INHIBITION_LOW:
        alerts.append(Alert(
            "Impulsivity", "warning",
            f"{fr(inhibition.mean(), 0)}% of statues held in front of the ogre on average: "
            "the child struggles to hold back movement.",
        ))

    fade = attention_fade(history).tail(3)
    if len(fade) >= 2 and fade.mean() >= ATTENTION_FADE:
        alerts.append(Alert(
            "Fading attention", "info",
            f"Success drops by {fr(fade.mean(), 0)} points between the start and end of the game: "
            "the game may be too long.",
        ))

    last_date = latest.get("session_date")
    if pd.notna(last_date):
        idle = (reference.normalize() - pd.Timestamp(last_date).normalize()).days
        if idle > INACTIVE_DAYS:
            alerts.append(Alert(
                "Inactive", "info",
                f"No session for {idle} days.",
            ))
    return alerts


def patient_status(history: pd.DataFrame, alerts: list[Alert]) -> str:
    if history.empty:
        return "New"
    if any(a.level in {"critical", "warning"} for a in alerts):
        return "Needs attention"
    slope = score_slope(history["score"].tail(TREND_WINDOW))
    amplitude_gain = recent_change(amplitude_series(history))
    abduction_gain = recent_change(abduction_series(history))
    sequence_gain = recent_change(sequence_series(history))
    inhibition_gain = recent_change(inhibition_series(history))
    if (inhibition_gain is not None and inhibition_gain >= INHIBITION_GAIN) or (slope is not None and slope >= TREND_SIGNIFICANT) or (
        amplitude_gain is not None and amplitude_gain >= AMPLITUDE_GAIN
    ) or (abduction_gain is not None and abduction_gain >= ABDUCTION_GAIN) or (
        sequence_gain is not None and sequence_gain >= SEQUENCE_GAIN
    ):
        return "Improving"
    return "Stable"


def patient_overview(patients: pd.DataFrame, sessions: pd.DataFrame,
                     reference: pd.Timestamp) -> pd.DataFrame:
    """Une ligne par patient : volume, dernières valeurs, tendance, statut, alertes."""
    rows = []
    grouped = {pid: grp.sort_values("session_date") for pid, grp in sessions.groupby("patient_id")}
    for patient in patients.itertuples(index=False):
        history = grouped.get(patient.id, sessions.iloc[0:0])
        alerts = patient_alerts(history, reference)
        latest = history.iloc[-1] if not history.empty else None
        recent = history.tail(TREND_WINDOW)
        rows.append({
            "id": patient.id,
            "full_name": patient.full_name,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "patient_code": patient.patient_code,
            "age": patient.age,
            "sessions": len(history),
            "games": history["game_name"].nunique() if not history.empty else 0,
            "last_session": latest["session_date"] if latest is not None else pd.NaT,
            "last_score": latest["score"] if latest is not None else np.nan,
            "last_success": latest["success_rate"] if latest is not None else np.nan,
            "recent_success": _mean(recent["success_rate"]) if not recent.empty else np.nan,
            "trend": score_slope(recent["score"]) if not recent.empty else None,
            "scores": history["score"].dropna().tail(12).tolist(),
            "status": patient_status(history, alerts),
            "has_account": bool(getattr(patient, "has_account", False)),
            "alerts": alerts,
        })
    overview = pd.DataFrame(rows)
    if overview.empty:
        return overview
    overview["status_rank"] = overview["status"].map({s: i for i, s in enumerate(STATUS_ORDER)})
    return overview


# ==========================================================
# SYNTHÈSE PAR JEU
# ==========================================================

def game_summary(sessions: pd.DataFrame) -> pd.DataFrame:
    if sessions.empty:
        return pd.DataFrame(columns=[
            "game_name", "sessions", "patients", "score", "success_rate",
            "duration_min", "repetitions", "progression",
        ])
    return (
        sessions.groupby("game_name")
        .agg(
            sessions=("patient_id", "size"),
            patients=("patient_id", "nunique"),
            score=("score", "mean"),
            success_rate=("success_rate", "mean"),
            duration_min=("duration_min", "mean"),
            repetitions=("repetitions", "mean"),
            progression=("progression", "mean"),
        )
        .reset_index()
        .sort_values("success_rate", ascending=False)
    )


def patient_game_matrix(sessions: pd.DataFrame, value: str = "success_rate") -> pd.DataFrame:
    if sessions.empty:
        return pd.DataFrame()
    return sessions.pivot_table(
        index="patient_name", columns="game_name", values=value, aggfunc="mean"
    ).sort_index()


def level_summary(sessions: pd.DataFrame) -> pd.DataFrame:
    df = sessions.dropna(subset=["level"])
    if df.empty:
        return pd.DataFrame(columns=["game_name", "level", "sessions", "success_rate", "score"])
    return (
        df.groupby(["game_name", "level"])
        .agg(sessions=("patient_id", "size"), success_rate=("success_rate", "mean"),
             score=("score", "mean"))
        .reset_index()
    )


# ==========================================================
# INSIGHTS PATIENT (« SensAI Intelligence »)
# ==========================================================

@dataclass
class Insight:
    title: str
    text: str
    tone: str  # "positive" | "warning" | "neutral"
    icon: str


def patient_insights(history: pd.DataFrame, reference: pd.Timestamp) -> list[Insight]:
    insights: list[Insight] = []
    if history.empty:
        return insights

    # 1. Tendance du score
    slope = score_slope(history["score"].tail(TREND_WINDOW))
    if slope is None:
        insights.append(Insight(
            "History still building",
            f"{len(history)} session(s) recorded: the trend will be calculated "
            f"from {MIN_SESSIONS_FOR_TREND} sessions.",
            "neutral", "◔",
        ))
    elif slope >= TREND_SIGNIFICANT:
        insights.append(Insight(
            "Improving score",
            f"{fr(slope, 1, True)} pt per session on average over recent sessions.",
            "positive", "↗",
        ))
    elif slope <= -TREND_SIGNIFICANT:
        insights.append(Insight(
            "Declining score",
            f"{fr(slope, 1, True)} pt per session over recent sessions: "
            "consider adjusting the difficulty.",
            "warning", "↘",
        ))
    else:
        insights.append(Insight(
            "Stable score",
            "No marked change in score over recent sessions.",
            "neutral", "→",
        ))

    # 2. Depuis le début du suivi
    first, last = history.iloc[0], history.iloc[-1]
    if len(history) >= 2 and pd.notna(first["success_rate"]) and pd.notna(last["success_rate"]):
        change = last["success_rate"] - first["success_rate"]
        tone = "positive" if change > 2 else "warning" if change < -2 else "neutral"
        insights.append(Insight(
            "Since the first session",
            f"Success {fr(first['success_rate'], 0)}% → {fr(last['success_rate'], 0)}% "
            f"({fr(change, 1, True)} pts).",
            tone, "◎",
        ))

    # 2 bis. Amplitude de rotation (Le Hibou)
    if {"rotation_left", "rotation_right"} <= set(history.columns):
        rot = history.dropna(subset=["rotation_left", "rotation_right"])
        if not rot.empty:
            last_rot = rot.iloc[-1]
            left, right = float(last_rot["rotation_left"]), float(last_rot["rotation_right"])
            target = last_rot.get("target_angle")
            sym = symmetry(left, right)
            goal = f" (target {fr(target, 0)}°)" if target is not None and pd.notna(target) else ""
            reached = target is not None and pd.notna(target) and min(left, right) >= target
            gain = ""
            if len(rot) >= 2:
                first_rot = rot.iloc[0]
                change = (left + right) / 2 - (float(first_rot["rotation_left"]) + float(first_rot["rotation_right"])) / 2
                gain = f" Average range {fr(change, 0, True)}° since the start."
            insights.append(Insight(
                "Cervical range of motion",
                f"Left {fr(left, 0)}° · right {fr(right, 0)}°{goal}, symmetry {fr(sym, 0)}%.{gain}",
                "positive" if reached and sym >= 80 else "warning" if sym < 70 else "neutral",
                "↔",
            ))

    # 2 ter. Abduction de l'épaule (Gardien des Lucioles)
    if "abduction_max" in history.columns:
        abd = history.dropna(subset=["abduction_max"])
        if not abd.empty:
            last_abd = abd.iloc[-1]
            peak, best = last_abd.get("abduction_mean_peak"), float(last_abd["abduction_max"])
            threshold = last_abd.get("target_angle")
            goal = f" (threshold {fr(threshold, 0)}°)" if threshold is not None and pd.notna(threshold) else ""
            reached = threshold is not None and pd.notna(threshold) and pd.notna(peak) and peak >= threshold
            gain = ""
            if len(abd) >= 2 and pd.notna(peak) and pd.notna(abd.iloc[0].get("abduction_mean_peak")):
                change = float(peak) - float(abd.iloc[0]["abduction_mean_peak"])
                gain = f" Mean peak {fr(change, 0, True)}° since the start."
            comp = last_abd.get("compensations")
            comp_text = f", {fr(comp, 0)} compensation(s)" if comp is not None and pd.notna(comp) else ""
            insights.append(Insight(
                "Shoulder abduction",
                f"Arm raised up to {fr(best, 0)}°{goal}{comp_text}.{gain}",
                "positive" if reached and not (pd.notna(comp) and comp >= COMPENSATION_HIGH) else "neutral",
                "↑",
            ))

    # 2 quater. Mémoire de séquence (Danse des Lucioles)
    if "max_sequence" in history.columns:
        seq = history.dropna(subset=["max_sequence"])
        if not seq.empty:
            last_seq = seq.iloc[-1]
            best = float(seq["max_sequence"].max())
            errs = last_seq.get("sequence_errors")
            hints = last_seq.get("hints_used")
            gain = ""
            if len(seq) >= 2:
                change = float(last_seq["max_sequence"]) - float(seq.iloc[0]["max_sequence"])
                gain = f" Sequence {fr(change, 0, True)} flower(s) since the start."
            details = []
            if errs is not None and pd.notna(errs):
                details.append(f"{fr(errs, 0)} error(s)")
            if hints is not None and pd.notna(hints):
                details.append(f"{fr(hints, 0)} hint(s)")
            insights.append(Insight(
                "Memory and coordination",
                f"Longest dance: {fr(last_seq['max_sequence'], 0)} flowers (best {fr(best, 0)})"
                + (f", {', '.join(details)}" if details else "") + f".{gain}",
                "positive" if gain and change > 0 else "neutral",
                "✿",
            ))

    # 2 quinquies. Attention et contrôle des gestes (Gardien du Château)
    if "nogo_success_rate" in history.columns:
        castle = history.dropna(subset=["nogo_success_rate"])
        if not castle.empty:
            last_c = castle.iloc[-1]
            parts = [f"challenges completed {fr(last_c.get('go_success_rate'), 0)}%",
                     f"statues held {fr(last_c['nogo_success_rate'], 0)}%"]
            rt = last_c.get("rt_mean_ms")
            if rt is not None and pd.notna(rt):
                parts.append(f"reaction {fr(rt, 0)} ms")
            gain = ""
            change = 0.0
            if len(castle) >= 2:
                change = float(last_c["nogo_success_rate"]) - float(castle.iloc[0]["nogo_success_rate"])
                gain = f" Control {fr(change, 0, True)} points since the start."
            insights.append(Insight(
                "Attention and movement control",
                f"Last game: {', '.join(parts)}.{gain}",
                "positive" if change > 0 else "neutral",
                "♜",
            ))

    # 3. Meilleur / plus difficile jeu
    games = history.groupby("game_name")["success_rate"].mean().dropna()
    if len(games) >= 2:
        best, hardest = games.idxmax(), games.idxmin()
        insights.append(Insight(
            "Strengths and areas to work on",
            f"Best success on “{best}” ({fr(games[best], 0)}%), "
            f"hardest on “{hardest}” ({fr(games[hardest], 0)}%).",
            "neutral", "◆",
        ))

    # 4. Assiduité (4 dernières semaines)
    window_start = reference.normalize() - pd.Timedelta(days=27)
    recent = history[history["session_date"] >= window_start]
    per_week = len(recent) / 4
    last_date = pd.Timestamp(last["session_date"]).normalize() if pd.notna(last["session_date"]) else None
    idle = (reference.normalize() - last_date).days if last_date is not None else None
    if idle is not None and idle > INACTIVE_DAYS:
        insights.append(Insight(
            "Attendance needs follow-up",
            f"Last session {idle} days ago.",
            "warning", "◷",
        ))
    else:
        insights.append(Insight(
            "Attendance",
            f"{fr(per_week, 1)} session(s) per week over the last 4 weeks.",
            "positive" if per_week >= 2 else "neutral", "◷",
        ))
    return insights


def symmetry(left: float, right: float) -> float:
    """Indice de symétrie gauche/droite en % (100 = parfaitement symétrique)."""
    if not left or not right or pd.isna(left) or pd.isna(right):
        return 0.0
    return min(left, right) / max(left, right) * 100


def first_vs_last(history: pd.DataFrame) -> pd.DataFrame:
    """Comparaison première / dernière séance pour chaque jeu."""
    rows = []
    for game, grp in history.sort_values("session_date").groupby("game_name"):
        first, last = grp.iloc[0], grp.iloc[-1]
        rows.append({
            "game_name": game,
            "sessions": len(grp),
            "first_score": first["score"],
            "last_score": last["score"],
            "first_success": first["success_rate"],
            "last_success": last["success_rate"],
            "first_level": first["level"],
            "last_level": last["level"],
        })
    return pd.DataFrame(rows)
