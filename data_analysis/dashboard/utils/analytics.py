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
INACTIVE_DAYS = 14          # jours sans séance avant alerte d'assiduité
TREND_WINDOW = 5            # nombre de séances pour la tendance récente
TREND_SIGNIFICANT = 1.0     # points de score par séance (pente)
MIN_SESSIONS_FOR_TREND = 3

STATUS_ORDER = ["À surveiller", "En progression", "Stable", "Nouveau"]


def fr(value: float, decimals: int = 1, signed: bool = False) -> str:
    """Nombre au format français (virgule décimale)."""
    text = f"{value:{'+' if signed else ''}.{decimals}f}"
    return text.replace(".", ",")


# ==========================================================
# PÉRIODES
# ==========================================================

PERIODS = {
    "7 jours": 7,
    "30 jours": 30,
    "90 jours": 90,
    "Tout": None,
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


def patient_alerts(history: pd.DataFrame, reference: pd.Timestamp) -> list[Alert]:
    """Signaux d'attention pour un patient (historique trié par date)."""
    alerts: list[Alert] = []
    if history.empty:
        return alerts
    latest = history.iloc[-1]

    success = latest.get("success_rate")
    if pd.notna(success) and success < LOW_SUCCESS:
        alerts.append(Alert(
            "Réussite faible", "critical",
            f"{fr(success, 0)} % de réussite à la dernière séance (seuil {fr(LOW_SUCCESS, 0)} %).",
        ))

    slope = score_slope(history["score"].tail(TREND_WINDOW))
    if slope is not None and slope <= -TREND_SIGNIFICANT:
        alerts.append(Alert(
            "Score en baisse", "warning",
            f"{fr(slope, 1, True)} pt de score par séance (5 dernières séances).",
        ))

    last_date = latest.get("session_date")
    if pd.notna(last_date):
        idle = (reference.normalize() - pd.Timestamp(last_date).normalize()).days
        if idle > INACTIVE_DAYS:
            alerts.append(Alert(
                "Inactif", "info",
                f"Aucune séance depuis {idle} jours.",
            ))
    return alerts


def patient_status(history: pd.DataFrame, alerts: list[Alert]) -> str:
    if history.empty:
        return "Nouveau"
    if any(a.level in {"critical", "warning"} for a in alerts):
        return "À surveiller"
    slope = score_slope(history["score"].tail(TREND_WINDOW))
    if slope is not None and slope >= TREND_SIGNIFICANT:
        return "En progression"
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
# INSIGHTS PATIENT (« KineKids Intelligence »)
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
            "Historique en construction",
            f"{len(history)} séance(s) enregistrée(s) : la tendance sera calculée "
            f"à partir de {MIN_SESSIONS_FOR_TREND} séances.",
            "neutral", "◔",
        ))
    elif slope >= TREND_SIGNIFICANT:
        insights.append(Insight(
            "Score en progression",
            f"{fr(slope, 1, True)} pt par séance en moyenne sur les dernières séances.",
            "positive", "↗",
        ))
    elif slope <= -TREND_SIGNIFICANT:
        insights.append(Insight(
            "Score en baisse",
            f"{fr(slope, 1, True)} pt par séance sur les dernières séances : "
            "envisager d’adapter la difficulté.",
            "warning", "↘",
        ))
    else:
        insights.append(Insight(
            "Score stable",
            "Pas de variation marquée du score sur les dernières séances.",
            "neutral", "→",
        ))

    # 2. Depuis le début du suivi
    first, last = history.iloc[0], history.iloc[-1]
    if len(history) >= 2 and pd.notna(first["success_rate"]) and pd.notna(last["success_rate"]):
        change = last["success_rate"] - first["success_rate"]
        tone = "positive" if change > 2 else "warning" if change < -2 else "neutral"
        insights.append(Insight(
            "Depuis la première séance",
            f"Réussite {fr(first['success_rate'], 0)} % → {fr(last['success_rate'], 0)} % "
            f"({fr(change, 1, True)} pts).",
            tone, "◎",
        ))

    # 3. Meilleur / plus difficile jeu
    games = history.groupby("game_name")["success_rate"].mean().dropna()
    if len(games) >= 2:
        best, hardest = games.idxmax(), games.idxmin()
        insights.append(Insight(
            "Points forts et axes de travail",
            f"Meilleure réussite sur « {best} » ({fr(games[best], 0)} %), "
            f"plus difficile sur « {hardest} » ({fr(games[hardest], 0)} %).",
            "neutral", "◆",
        ))
    elif len(games) == 1:
        insights.append(Insight(
            "Un seul jeu pratiqué",
            f"Toutes les séances portent sur « {games.index[0]} ». "
            "Varier les jeux élargit l’évaluation motrice.",
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
            "Assiduité à relancer",
            f"Dernière séance il y a {idle} jours.",
            "warning", "◷",
        ))
    else:
        insights.append(Insight(
            "Assiduité",
            f"{fr(per_week, 1)} séance(s) par semaine sur les 4 dernières semaines.",
            "positive" if per_week >= 2 else "neutral", "◷",
        ))
    return insights


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
