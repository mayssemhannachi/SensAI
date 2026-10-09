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
    "knee": "Genou", "wrist": "Poignet", "shoulder": "Épaule", "elbow": "Coude",
    "hip": "Hanche", "ankle": "Cheville", "neck": "Cou", "trunk": "Tronc", "hand": "Main",
}


def show_games():
    data = load_dataset()
    reference = data.reference_date
    sessions_all = data.sessions

    page_header(
        "Activité thérapeutique",
        "Analyse par jeu",
        "Comparez les jeux SensAI : réussite, difficulté par niveau et patients concernés.",
        meta=f"{sessions_all['game_name'].nunique()} jeu(x) joué(s) · {len(data.games)} au catalogue",
    )

    if sessions_all.empty:
        empty_state("🎮", "Aucune séance enregistrée",
                    "Les statistiques par jeu apparaîtront dès les premières séances.")
        return

    period_col, _ = st.columns([1.3, 2], vertical_alignment="bottom")
    with period_col:
        period = st.segmented_control(
            "Période", list(analytics.PERIODS), default="Tout", key="games_period"
        ) or "Tout"
    sessions = analytics.filter_period(sessions_all, analytics.PERIODS[period], reference)
    if sessions.empty:
        empty_state("🗓️", "Aucune séance sur cette période", "Élargissez la période.")
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
        foot = f"{row.patients} patient(s) · {fmt_number(row.duration_min, 1)} min/séance"
        with columns[index % len(columns)]:
            render_html(
                kpi_card(
                    row.game_name,
                    fmt_number(row.success_rate, 1),
                    icon=f"<span style='width:12px;height:12px;border-radius:4px;"
                         f"background:{colors.get(row.game_name)}'></span>",
                    tone="tone-blue",
                    unit=" %",
                    foot=(f"{part} · " if isinstance(part, str) else "") + foot,
                    delta_html=f"<span class='kk-delta flat'>{row.sessions} séances</span>",
                )
            )

    # --------------------------------------------------------
    # COMPARAISON & ÉVOLUTION
    # --------------------------------------------------------
    section("Comparaison", "Réussite moyenne par jeu et son évolution hebdomadaire.")
    left, right = st.columns([1, 1.5], gap="medium")
    with left:
        with card("games-compare"):
            card_title("Réussite moyenne", "Toutes séances de la période.")
            st.plotly_chart(charts.game_comparison_chart(summary, colors), config=charts.CHART_CONFIG,
                            key="games_compare")
    with right:
        with card("games-weekly"):
            card_title("Réussite par semaine", "Moyenne hebdomadaire de chaque jeu.")
            st.plotly_chart(charts.game_weekly_chart(sessions, colors), config=charts.CHART_CONFIG,
                            key="games_weekly")

    # --------------------------------------------------------
    # NIVEAUX
    # --------------------------------------------------------
    levels = analytics.level_summary(sessions)
    if not levels.empty:
        section("Difficulté par niveau", "Réussite moyenne selon le niveau de l’exercice.")
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
        section("Patients × jeux", "Réussite moyenne de chaque patient sur chaque jeu (case vide = jeu non pratiqué).")
        with card("matrix"):
            st.plotly_chart(charts.heatmap_chart(matrix), config=charts.CHART_CONFIG, key="games_matrix")

    # --------------------------------------------------------
    # TABLEAU
    # --------------------------------------------------------
    section("Détail", "Indicateurs moyens par jeu.")
    table = summary.rename(columns={
        "game_name": "Jeu", "sessions": "Séances", "patients": "Patients", "score": "Score moyen",
        "success_rate": "Réussite", "duration_min": "Durée moy. (min)",
        "repetitions": "Répétitions moy.", "progression": "Progression moy.",
    })
    st.dataframe(
        table, hide_index=True, width="stretch",
        column_config={
            "Score moyen": st.column_config.NumberColumn(format="%.1f"),
            "Réussite": st.column_config.ProgressColumn(format="%.1f %%", min_value=0, max_value=100),
            "Durée moy. (min)": st.column_config.NumberColumn(format="%.1f"),
            "Répétitions moy.": st.column_config.NumberColumn(format="%.1f"),
            "Progression moy.": st.column_config.NumberColumn(format="%+.1f %%"),
        },
    )
    unused = set(data.games["name"].dropna()) - set(sessions_all["game_name"])
    if unused:
        render_html(
            "<div class='kk-note'><b>ⓘ</b><div>Jeux à venir dans SensAI (pas encore de séance) : "
            + ", ".join(esc(name) for name in sorted(unused)) + ".</div></div>"
        )
