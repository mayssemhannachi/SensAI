import pandas as pd
import streamlit as st

from dashboard import navigation
from dashboard.components import charts
from dashboard.components.ui import (
    alert_badges,
    avatar,
    card,
    card_title,
    delta_chip,
    empty_state,
    esc,
    fmt_date,
    fmt_number,
    kpi_card,
    kpi_row,
    note,
    page_header,
    render_html,
    section,
)
from dashboard.utils import analytics
from dashboard.utils.data import load_dataset


def _period_label(days):
    return "tout l’historique" if days is None else f"les {days} derniers jours"


def show_global_view():
    data = load_dataset()
    reference = data.reference_date
    sessions_all = data.sessions

    last_data = sessions_all["session_date"].max() if not sessions_all.empty else None
    page_header(
        "Espace thérapeute · suivi pédiatrique",
        "Vue d’ensemble",
        "L’activité, les performances et les patients qui demandent votre attention, en un coup d’œil.",
        meta=f"<span class='kk-dot on'></span>Dernière séance : {fmt_date(last_data)}",
    )

    if data.patients.empty:
        empty_state("👋", "Aucun patient pour le moment",
                    "Ajoutez un premier patient pour commencer le suivi.")
        if st.button("＋ Ajouter un patient", type="primary"):
            navigation.go("add_patient")
        return

    if sessions_all.empty:
        empty_state("🎮", "Aucune séance enregistrée",
                    "Les indicateurs apparaîtront dès que les jeux enverront leurs premières séances.")
        return

    # --------------------------------------------------------
    # PÉRIODE
    # --------------------------------------------------------
    period_col, info_col = st.columns([1.3, 2], vertical_alignment="bottom")
    with period_col:
        period = st.segmented_control(
            "Période d’analyse",
            list(analytics.PERIODS),
            default="30 jours",
            key="overview_period",
        ) or "30 jours"
    days = analytics.PERIODS[period]
    current = analytics.filter_period(sessions_all, days, reference)
    previous = analytics.previous_period(sessions_all, days, reference)
    start, _ = analytics.period_bounds(sessions_all, days, reference)
    with info_col:
        render_html(
            f"<div style='text-align:right;font-size:12.5px;color:#667085;padding-bottom:6px'>"
            f"Du <b>{fmt_date(start)}</b> au <b>{fmt_date(reference)}</b>"
            f"{' · comparé à la période précédente' if days else ''}</div>"
        )

    overview = analytics.patient_overview(data.patients, sessions_all, reference)
    watch = overview[overview["status"] == "À surveiller"] if not overview.empty else overview

    # --------------------------------------------------------
    # KPI
    # --------------------------------------------------------
    k = analytics.global_kpis(current, previous)
    vs = "vs période précédente" if days else "sur tout l’historique"
    kpi_row([
        kpi_card("Patients actifs", fmt_number(k["patients"]["value"]), "◉", "tone-violet",
                 foot=f"sur {len(data.patients)} suivis",
                 delta_html=delta_chip(k["patients"]["delta"], decimals=0)),
        kpi_card("Séances réalisées", fmt_number(k["sessions"]["value"]), "▶", "tone-blue",
                 foot=vs, delta_html=delta_chip(k["sessions"]["delta"], decimals=0)),
        kpi_card("Réussite moyenne", fmt_number(k["success"]["value"], 1), "✓", "tone-green",
                 unit=" %", foot=vs, delta_html=delta_chip(k["success"]["delta"], " pts")),
        kpi_card("Score moyen", fmt_number(k["score"]["value"], 1), "★", "tone-orange",
                 foot=vs, delta_html=delta_chip(k["score"]["delta"], " pt")),
        kpi_card("À surveiller", fmt_number(len(watch)), "!", "tone-pink",
                 foot="patients avec un signal actif"),
    ])

    if current.empty:
        st.write("")
        empty_state("🗓️", "Aucune séance sur cette période",
                    "Élargissez la période d’analyse pour voir les tendances.")
        return

    # --------------------------------------------------------
    # TENDANCES
    # --------------------------------------------------------
    section("Tendances", f"Évolution hebdomadaire sur {_period_label(days)}.")
    left, right = st.columns([1.7, 1], gap="medium")
    with left:
        with card("trend"):
            card_title("Score et réussite par semaine",
                       "Moyenne de toutes les séances de la semaine (échelle 0–100).")
            weekly = analytics.weekly_trend(current)
            st.plotly_chart(charts.weekly_trend_chart(weekly), config=charts.CHART_CONFIG,
                            key="overview_weekly")
    with right:
        with card("distribution"):
            card_title("Répartition des taux de réussite", "Nombre de séances par tranche.")
            st.plotly_chart(
                charts.success_distribution_chart(analytics.success_distribution(current)),
                config=charts.CHART_CONFIG, key="overview_distribution",
            )

    # --------------------------------------------------------
    # JEUX + PATIENTS À SURVEILLER
    # --------------------------------------------------------
    section("Jeux et vigilance", "Comparer les activités et repérer les patients à revoir.")
    left, right = st.columns([1.15, 1], gap="medium")
    colors = charts.game_colors(sessions_all["game_name"])
    with left:
        with card("games"):
            has_rotation = current[["rotation_left", "rotation_right"]].notna().any().any()
            if current["game_name"].nunique() <= 1 and has_rotation:
                card_title("Amplitude cervicale moyenne",
                           "Rotation moyenne atteinte par semaine (tous patients), et angle cible moyen.")
                st.plotly_chart(charts.weekly_amplitude_chart(current), config=charts.CHART_CONFIG,
                                key="overview_amplitude")
            else:
                card_title("Réussite moyenne par jeu", "Survolez une barre pour le détail.")
                summary = analytics.game_summary(current)
                st.plotly_chart(charts.game_comparison_chart(summary, colors), config=charts.CHART_CONFIG,
                                key="overview_games")
            if st.button("Voir l’analyse par jeu →", key="overview_to_games"):
                navigation.go("games")
    with right:
        with card("watch"):
            card_title(f"Patients à surveiller ({len(watch)})",
                       "Signaux calculés sur l’historique complet de chaque patient.")
            if watch.empty:
                render_html(
                    "<div class='kk-watch'><span class='kk-badge good'>✓</span>"
                    "<div class='kk-watch-detail'>Aucun signal d’alerte : tous les patients "
                    "suivent une trajectoire stable ou en progression.</div></div>"
                )
            else:
                ordered = watch.assign(
                    _n=watch["alerts"].map(lambda a: -sum(x.level == "critical" for x in a))
                ).sort_values(["_n", "trend"])
                for row in ordered.head(6).itertuples(index=False):
                    info, action = st.columns([4, 1.1], vertical_alignment="center")
                    with info:
                        detail = row.alerts[0].detail if row.alerts else ""
                        render_html(
                            f"""
                            <div class="kk-watch">
                              {avatar(row.first_name, row.last_name, seed=row.id)}
                              <div>
                                <div class="kk-watch-name">{esc(row.full_name)}</div>
                                <div class="kk-alerts" style="margin-top:3px">{alert_badges(row.alerts)}</div>
                                <div class="kk-watch-detail">{esc(detail)}</div>
                              </div>
                            </div>
                            """
                        )
                    with action:
                        if st.button("Fiche", key=f"watch_{row.id}", width="stretch"):
                            navigation.open_patient(row.id)
                if len(watch) > 6:
                    if st.button(f"Voir les {len(watch)} patients à surveiller →", key="watch_all"):
                        st.session_state["patients_status_filter"] = ["À surveiller"]
                        navigation.go("patients")
            note("ces signaux sont une aide à la décision et doivent être interprétés "
                 "dans leur contexte clinique.", title="Aide à la décision")

    # --------------------------------------------------------
    # DERNIÈRES SÉANCES
    # --------------------------------------------------------
    section("Dernières séances", "Les 10 séances les plus récentes de la période.")
    recent = current.sort_values("session_date", ascending=False).head(10)
    table = pd.DataFrame({
        "Date": recent["session_date"],
        "Patient": recent["patient_name"],
        "Jeu": recent["game_name"],
        "Niveau": recent["level"],
        "Score": recent["score"],
        "Réussite": recent["success_rate"],
        "Progression": recent["progression"],
        "Rot. G (°)": recent["rotation_left"],
        "Rot. D (°)": recent["rotation_right"],
        "Abd. max (°)": recent["abduction_max"],
        "Séq. max": recent["max_sequence"],
        "Douleur (/5)": recent["pain_level"],
        "Durée": recent["duration_min"],
    })
    optional = ["Rot. G (°)", "Rot. D (°)", "Abd. max (°)", "Séq. max", "Douleur (/5)"]
    table = table.drop(columns=[c for c in optional if table[c].isna().all()])
    if any(c in table.columns for c in optional):
        table = table.drop(columns=["Progression"])
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            "Date": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
            "Niveau": st.column_config.NumberColumn(format="%d"),
            "Score": st.column_config.NumberColumn(format="%.1f"),
            "Réussite": st.column_config.ProgressColumn(format="%.0f %%", min_value=0, max_value=100),
            "Progression": st.column_config.NumberColumn(format="%+.1f %%"),
            "Durée": st.column_config.NumberColumn("Durée (min)", format="%.1f"),
            "Rot. G (°)": st.column_config.NumberColumn(format="%d"),
            "Rot. D (°)": st.column_config.NumberColumn(format="%d"),
            "Abd. max (°)": st.column_config.NumberColumn(format="%d"),
            "Séq. max": st.column_config.NumberColumn(format="%d"),
            "Douleur (/5)": st.column_config.NumberColumn(format="%d"),
        },
    )
