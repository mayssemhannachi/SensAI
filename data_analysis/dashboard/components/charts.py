"""Graphiques Plotly du dashboard — un seul style, une seule palette.

Règles : un seul axe Y par graphique, une couleur suit toujours la même entité
(métrique ou jeu), info-bulles systématiques, grille discrète.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from dashboard.utils.theme import COLORS, METRIC_COLORS, SEQUENTIAL, SERIES

CHART_CONFIG = {"displayModeBar": False, "responsive": True}

METRIC_LABELS = {
    "score": "Score",
    "success_rate": "Réussite (%)",
}


def game_colors(game_names) -> dict:
    """Couleur fixe par jeu (ordre alphabétique → créneau de palette)."""
    names = sorted({str(n) for n in game_names if pd.notna(n)})
    return {name: SERIES[i % len(SERIES)] for i, name in enumerate(names)}


def _layout(fig: go.Figure, height: int = 320, legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=12, t=10, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color=COLORS["text_secondary"], size=12),
        separators=", ",
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    title_text="", font=dict(size=12), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=COLORS["border"],
                        font=dict(family="DM Sans, sans-serif", size=12, color=COLORS["text"])),
        bargap=0.35,
    )
    fig.update_xaxes(showgrid=False, linecolor=COLORS["border"], ticks="",
                     tickfont=dict(color=COLORS["muted"], size=11), title_font=dict(size=11, color=COLORS["muted"]))
    fig.update_yaxes(showgrid=True, gridcolor=COLORS["grid"], zeroline=False, linecolor="rgba(0,0,0,0)",
                     tickfont=dict(color=COLORS["muted"], size=11), title_font=dict(size=11, color=COLORS["muted"]))
    return fig


# ============================================================
# VUE GLOBALE
# ============================================================

def weekly_trend_chart(weekly: pd.DataFrame) -> go.Figure:
    """Score moyen et réussite moyenne par semaine (même échelle 0-100)."""
    fig = go.Figure()
    for metric in ["score", "success_rate"]:
        color = METRIC_COLORS[metric]
        label = "Score moyen" if metric == "score" else "Réussite moyenne (%)"
        unit = "" if metric == "score" else " %"
        fig.add_trace(go.Scatter(
            x=weekly["week"], y=weekly[metric], name=label, mode="lines+markers",
            line=dict(color=color, width=2.5),
            marker=dict(size=8, color="#FFFFFF", line=dict(color=color, width=2)),
            customdata=weekly[["sessions", "patients"]],
            hovertemplate=(f"<b>{label}</b> : %{{y:.1f}}{unit}<br>"
                           "%{customdata[0]} séances · %{customdata[1]} patients<extra></extra>"),
        ))
    fig.update_xaxes(tickformat="%d/%m", hoverformat="Semaine du %d/%m/%Y")
    fig.update_layout(hovermode="x unified")
    return _layout(fig, height=330)


def success_distribution_chart(distribution: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=distribution["range"], y=distribution["count"],
        marker=dict(color=METRIC_COLORS["success_rate"], cornerradius=4),
        hovertemplate="Réussite %{x} %<br><b>%{y} séances</b><extra></extra>",
        text=distribution["count"], textposition="outside", textfont=dict(size=11, color=COLORS["muted"]),
        cliponaxis=False,
    ))
    fig.update_yaxes(title_text="Séances")
    fig.update_xaxes(title_text="Taux de réussite (%)", tickangle=0)
    return _layout(fig, height=330, legend=False)


def game_comparison_chart(summary: pd.DataFrame, colors: dict) -> go.Figure:
    data = summary.sort_values("success_rate")
    fig = go.Figure(go.Bar(
        y=data["game_name"], x=data["success_rate"], orientation="h",
        marker=dict(color=[colors.get(g, COLORS["primary"]) for g in data["game_name"]], cornerradius=4),
        customdata=data[["sessions", "patients", "score"]],
        text=[f"{v:.0f} %" if pd.notna(v) else "" for v in data["success_rate"]],
        textposition="outside", textfont=dict(size=12, color=COLORS["text"]), cliponaxis=False,
        hovertemplate=("<b>%{y}</b><br>Réussite moyenne : %{x:.1f} %<br>Score moyen : %{customdata[2]:.1f}"
                       "<br>%{customdata[0]} séances · %{customdata[1]} patients<extra></extra>"),
    ))
    fig.update_xaxes(range=[0, 100], showgrid=True, gridcolor=COLORS["grid"], ticksuffix=" %")
    fig.update_yaxes(showgrid=False)
    return _layout(fig, height=max(200, 70 * len(data) + 60), legend=False)


# ============================================================
# FICHE PATIENT
# ============================================================

def patient_metric_chart(history: pd.DataFrame, metric: str, colors: dict) -> go.Figure:
    """Points par séance colorés par jeu + moyenne glissante (3 séances)."""
    label = METRIC_LABELS[metric]
    unit = " %" if metric == "success_rate" else ""
    data = history.dropna(subset=[metric, "session_date"]).sort_values("session_date")
    fig = go.Figure()
    for game, group in data.groupby("game_name"):
        fig.add_trace(go.Scatter(
            x=group["session_date"], y=group[metric], mode="markers", name=str(game),
            marker=dict(size=9, color=colors.get(game, COLORS["primary"]), line=dict(color="#FFFFFF", width=2)),
            customdata=group[["level", "exercise_name"]].astype(object).where(group[["level", "exercise_name"]].notna(), "—"),
            hovertemplate=(f"<b>%{{x|%d/%m/%Y}}</b> · {game}<br>{label} : %{{y:.1f}}{unit}"
                           "<br>Niveau %{customdata[0]} · %{customdata[1]}<extra></extra>"),
        ))
    if len(data) >= 3:
        rolling = data[metric].rolling(3, min_periods=2).mean()
        fig.add_trace(go.Scatter(
            x=data["session_date"], y=rolling, mode="lines", name="Moyenne glissante (3 séances)",
            line=dict(color=COLORS["text"], width=2, dash="dot"),
            hovertemplate=f"Moyenne glissante : %{{y:.1f}}{unit}<extra></extra>",
        ))
    if metric == "success_rate":
        fig.update_yaxes(range=[0, 100], ticksuffix=" %")
    fig.update_xaxes(tickformat="%d/%m")
    return _layout(fig, height=340)


def progression_chart(history: pd.DataFrame) -> go.Figure:
    data = history.dropna(subset=["progression", "session_date"]).sort_values("session_date")
    colors = [COLORS["good"] if v >= 0 else COLORS["critical"] for v in data["progression"]]
    fig = go.Figure(go.Bar(
        x=data["session_date"], y=data["progression"], marker=dict(color=colors, cornerradius=3),
        customdata=data[["game_name"]],
        hovertemplate="<b>%{x|%d/%m/%Y}</b> · %{customdata[0]}<br>Variation : %{y:+.1f} %<extra></extra>",
    ))
    fig.add_hline(y=0, line=dict(color=COLORS["border"], width=1))
    fig.update_yaxes(ticksuffix=" %", title_text="Variation vs séance précédente")
    fig.update_xaxes(tickformat="%d/%m")
    return _layout(fig, height=320, legend=False)


def patient_games_chart(history: pd.DataFrame, colors: dict) -> go.Figure:
    summary = (
        history.groupby("game_name")
        .agg(success_rate=("success_rate", "mean"), score=("score", "mean"), sessions=("patient_id", "size"))
        .reset_index()
        .sort_values("success_rate")
    )
    return game_comparison_chart(summary.assign(patients=1), colors)


# ============================================================
# JEUX
# ============================================================

def heatmap_chart(matrix: pd.DataFrame, label: str = "Réussite moyenne (%)") -> go.Figure:
    scale = [[i / (len(SEQUENTIAL) - 1), c] for i, c in enumerate(SEQUENTIAL)]
    z = matrix.to_numpy()
    text = [[f"{v:.0f}" if pd.notna(v) else "" for v in row] for row in z]
    fig = go.Figure(go.Heatmap(
        z=z, x=list(matrix.columns), y=list(matrix.index), colorscale=scale, zmin=30, zmax=85,
        xgap=3, ygap=3, text=text, texttemplate="%{text}", textfont=dict(size=11),
        hovertemplate="<b>%{y}</b> · %{x}<br>" + label + " : %{z:.1f}<extra></extra>",
        colorbar=dict(title=dict(text="%", side="top"), thickness=10, outlinewidth=0, len=0.8),
        hoverongaps=False,
    ))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(side="top")
    return _layout(fig, height=max(320, 26 * len(matrix) + 90), legend=False)


def level_chart(levels: pd.DataFrame, color: str) -> go.Figure:
    data = levels.sort_values("level")
    fig = go.Figure(go.Bar(
        x=[f"Niveau {int(l)}" for l in data["level"]], y=data["success_rate"],
        marker=dict(color=color, cornerradius=4),
        customdata=data[["sessions", "score"]],
        text=[f"{v:.0f} %" for v in data["success_rate"]], textposition="outside",
        textfont=dict(size=11, color=COLORS["text"]), cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Réussite : %{y:.1f} %<br>Score : %{customdata[1]:.1f}"
                      "<br>%{customdata[0]} séances<extra></extra>",
    ))
    fig.update_yaxes(range=[0, 100], ticksuffix=" %")
    return _layout(fig, height=280, legend=False)


def game_weekly_chart(sessions: pd.DataFrame, colors: dict, metric: str = "success_rate") -> go.Figure:
    data = sessions.dropna(subset=["session_date", metric]).copy()
    data["week"] = data["session_date"].dt.to_period("W-SUN").dt.start_time
    weekly = data.groupby(["game_name", "week"])[metric].mean().reset_index()
    fig = go.Figure()
    for game, group in weekly.groupby("game_name"):
        fig.add_trace(go.Scatter(
            x=group["week"], y=group[metric], mode="lines+markers", name=str(game),
            line=dict(color=colors.get(game), width=2),
            marker=dict(size=7, color=colors.get(game), line=dict(color="#FFFFFF", width=1.5)),
            hovertemplate=f"<b>{game}</b> : %{{y:.1f}} %<extra></extra>",
        ))
    fig.update_yaxes(range=[0, 100], ticksuffix=" %")
    fig.update_xaxes(tickformat="%d/%m", hoverformat="Semaine du %d/%m/%Y")
    fig.update_layout(hovermode="x unified")
    return _layout(fig, height=330)
