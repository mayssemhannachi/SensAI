import streamlit as st

from dashboard.components import charts
from dashboard.components.ui import (
    card,
    card_title,
    empty_state,
    esc,
    fmt_number,
    kpi_card,
    kpi_row,
    page_header,
    render_html,
    section,
)
from dashboard.utils import analytics
from dashboard.utils.data import load_dataset


BODY_PARTS_FR = {
    "knee": "Knee", "wrist": "Wrist", "shoulder": "Shoulder", "elbow": "Elbow",
    "hip": "Hip", "ankle": "Ankle", "neck": "Neck", "trunk": "Trunk", "hand": "Hand",
}


def show_games():
    data = load_dataset()
    reference = data.reference_date
    sessions_all = data.sessions

    page_header(
        "Therapeutic activity",
        "Game analysis",
        "Compare SensAI games: success, difficulty by level and patients involved.",
        meta=f"{sessions_all['game_name'].nunique()} game(s) played · {len(data.games)} in catalog",
    )

    if sessions_all.empty:
        empty_state("🎮", "No sessions recorded",
                    "Game statistics will appear after the first sessions.")
        return

    period_col, _ = st.columns([1.3, 2], vertical_alignment="bottom")
    with period_col:
        period = st.segmented_control(
            "Period", list(analytics.PERIODS), default="All", key="games_period"
        ) or "All"
    sessions = analytics.filter_period(sessions_all, analytics.PERIODS[period], reference)
    if sessions.empty:
        empty_state("🗓️", "No sessions in this period", "Widen the period.")
        return

    colors = charts.game_colors(sessions_all["game_name"])
    summary = analytics.game_summary(sessions)

    # --------------------------------------------------------
    # CARTES PAR JEU
    # --------------------------------------------------------
    body_parts = data.games.set_index("name")["body_part"].to_dict() if not data.games.empty else {}
    columns = st.columns(min(len(summary), 4) or 1, gap="small")
    for index, row in enumerate(summary.itertuples(index=False)):
        part = body_parts.get(row.game_name)
        part = BODY_PARTS_FR.get(str(part).lower(), part) if isinstance(part, str) else None
        foot = f"{row.patients} patient(s) · {fmt_number(row.duration_min, 1)} min/session"
        with columns[index % len(columns)]:
            render_html(
                kpi_card(
                    row.game_name,
                    fmt_number(row.success_rate, 1),
                    icon=f"<span style='width:12px;height:12px;border-radius:4px;"
                         f"background:{colors.get(row.game_name)}'></span>",
                    tone="tone-blue",
                    unit="%",
                    foot=(f"{part} · " if isinstance(part, str) else "") + foot,
                    delta_html=f"<span class='kk-delta flat'>{row.sessions} sessions</span>",
                )
            )

    # --------------------------------------------------------
    # COMPARAISON & ÉVOLUTION
    # --------------------------------------------------------
    section("Comparison", "Average success by game and its weekly trend.")
    left, right = st.columns([1, 1.5], gap="medium")
    with left:
        with card("games-compare"):
            card_title("Average success", "All sessions in the period.")
            st.plotly_chart(charts.game_comparison_chart(summary, colors), config=charts.CHART_CONFIG,
                            key="games_compare")
    with right:
        with card("games-weekly"):
            card_title("Success by week", "Weekly average for each game.")
            st.plotly_chart(charts.game_weekly_chart(sessions, colors), config=charts.CHART_CONFIG,
                            key="games_weekly")

    # --------------------------------------------------------
    # NIVEAUX
    # --------------------------------------------------------
    levels = analytics.level_summary(sessions)
    if not levels.empty:
        section("Difficulty by level", "Average success by exercise level.")
        games = sorted(levels["game_name"].unique())
        columns = st.columns(min(len(games), 3), gap="medium")
        for index, game in enumerate(games):
            with columns[index % len(columns)]:
                with card(f"levels-{index}"):
                    card_title(game)
                    st.plotly_chart(
                        charts.level_chart(levels[levels["game_name"] == game], colors.get(game)),
                        config=charts.CHART_CONFIG, key=f"levels_{index}",
                    )

    # --------------------------------------------------------
    # MATRICE PATIENTS × JEUX
    # --------------------------------------------------------
    matrix = analytics.patient_game_matrix(sessions)
    if not matrix.empty:
        section("Patients × games", "Average success of each patient on each game (empty cell = game not played).")
        with card("matrix"):
            st.plotly_chart(charts.heatmap_chart(matrix), config=charts.CHART_CONFIG, key="games_matrix")

    # --------------------------------------------------------
    # TABLEAU
    # --------------------------------------------------------
    section("Details", "Average indicators by game.")
    table = summary.rename(columns={
        "game_name": "Game", "sessions": "Sessions", "patients": "Patients", "score": "Average score",
        "success_rate": "Success", "duration_min": "Avg. duration (min)",
        "repetitions": "Avg. repetitions", "progression": "Avg. progression",
    })
    st.dataframe(
        table, hide_index=True, width="stretch",
        column_config={
            "Average score": st.column_config.NumberColumn(format="%.1f"),
            "Success": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
            "Avg. duration (min)": st.column_config.NumberColumn(format="%.1f"),
            "Avg. repetitions": st.column_config.NumberColumn(format="%.1f"),
            "Avg. progression": st.column_config.NumberColumn(format="%+.1f%%"),
        },
    )
    unused = set(data.games["name"].dropna()) - set(sessions_all["game_name"])
    if unused:
        render_html(
            "<div class='kk-note'><b>ⓘ</b><div>Upcoming SensAI games (no sessions yet): "
            + ", ".join(esc(name) for name in sorted(unused)) + ".</div></div>"
        )
