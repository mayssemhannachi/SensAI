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
    return "the full history" if days is None else f"the last {days} days"


def show_global_view():
    data = load_dataset()
    reference = data.reference_date
    sessions_all = data.sessions

    last_data = sessions_all["session_date"].max() if not sessions_all.empty else None
    page_header(
        "Therapist space · pediatric follow-up",
        "Overview",
        "Activity, performance and the patients who need your attention, at a glance.",
        meta=f"<span class='kk-dot on'></span>Last session: {fmt_date(last_data)}",
    )

    if data.patients.empty:
        empty_state("👋", "No patients yet",
                    "Add a first patient to start follow-up.")
        if st.button("＋ Add a patient", type="primary"):
            navigation.go("add_patient")
        return

    if sessions_all.empty:
        empty_state("🎮", "No sessions recorded",
                    "Indicators will appear as soon as the games send their first sessions.")
        return

    # --------------------------------------------------------
    # PÉRIODE
    # --------------------------------------------------------
    period_col, info_col = st.columns([1.3, 2], vertical_alignment="bottom")
    with period_col:
        period = st.segmented_control(
            "Analysis period",
            list(analytics.PERIODS),
            default="30 days",
            key="overview_period",
        ) or "30 days"
    days = analytics.PERIODS[period]
    current = analytics.filter_period(sessions_all, days, reference)
    previous = analytics.previous_period(sessions_all, days, reference)
    start, _ = analytics.period_bounds(sessions_all, days, reference)
    with info_col:
        render_html(
            f"<div style='text-align:right;font-size:12.5px;color:#667085;padding-bottom:6px'>"
            f"From <b>{fmt_date(start)}</b> to <b>{fmt_date(reference)}</b>"
            f"{' · compared with the previous period' if days else ''}</div>"
        )

    overview = analytics.patient_overview(data.patients, sessions_all, reference)
    watch = overview[overview["status"] == "Needs attention"] if not overview.empty else overview

    # --------------------------------------------------------
    # KPI
    # --------------------------------------------------------
    k = analytics.global_kpis(current, previous)
    vs = "vs previous period" if days else "over the full history"
    kpi_row([
        kpi_card("Active patients", fmt_number(k["patients"]["value"]), "◉", "tone-violet",
                 foot=f"of {len(data.patients)} followed",
                 delta_html=delta_chip(k["patients"]["delta"], decimals=0)),
        kpi_card("Sessions completed", fmt_number(k["sessions"]["value"]), "▶", "tone-blue",
                 foot=vs, delta_html=delta_chip(k["sessions"]["delta"], decimals=0)),
        kpi_card("Average success", fmt_number(k["success"]["value"], 1), "✓", "tone-green",
                 unit="%", foot=vs, delta_html=delta_chip(k["success"]["delta"], " pts")),
        kpi_card("Average score", fmt_number(k["score"]["value"], 1), "★", "tone-orange",
                 foot=vs, delta_html=delta_chip(k["score"]["delta"], " pt")),
        kpi_card("Needs attention", fmt_number(len(watch)), "!", "tone-pink",
                 foot="patients with an active signal"),
    ])

    if current.empty:
        st.write("")
        empty_state("🗓️", "No sessions in this period",
                    "Widen the analysis period to see trends.")
        return

    # --------------------------------------------------------
    # TENDANCES
    # --------------------------------------------------------
    section("Trends", f"Weekly trend over {_period_label(days)}.")
    left, right = st.columns([1.7, 1], gap="medium")
    with left:
        with card("trend"):
            card_title("Score and success by week",
                       "Average of all sessions in the week (0–100 scale).")
            weekly = analytics.weekly_trend(current)
            st.plotly_chart(charts.weekly_trend_chart(weekly), config=charts.CHART_CONFIG,
                            key="overview_weekly")
    with right:
        with card("distribution"):
            card_title("Success rate distribution", "Number of sessions per range.")
            st.plotly_chart(
                charts.success_distribution_chart(analytics.success_distribution(current)),
                config=charts.CHART_CONFIG, key="overview_distribution",
            )

    # --------------------------------------------------------
    # JEUX + PATIENTS À SURVEILLER
    # --------------------------------------------------------
    section("Games and watchlist", "Compare activities and spot patients to review.")
    left, right = st.columns([1.15, 1], gap="medium")
    colors = charts.game_colors(sessions_all["game_name"])
    with left:
        with card("games"):
            has_rotation = current[["rotation_left", "rotation_right"]].notna().any().any()
            if current["game_name"].nunique() <= 1 and has_rotation:
                card_title("Average cervical range of motion",
                           "Average rotation reached per week (all patients), and mean target angle.")
                st.plotly_chart(charts.weekly_amplitude_chart(current), config=charts.CHART_CONFIG,
                                key="overview_amplitude")
            else:
                card_title("Average success by game", "Hover over a bar for details.")
                summary = analytics.game_summary(current)
                st.plotly_chart(charts.game_comparison_chart(summary, colors), config=charts.CHART_CONFIG,
                                key="overview_games")
            if st.button("See game analysis →", key="overview_to_games"):
                navigation.go("games")
    with right:
        with card("watch"):
            card_title(f"Patients needing attention ({len(watch)})",
                       "Signals calculated from each patient's full history.")
            if watch.empty:
                render_html(
                    "<div class='kk-watch'><span class='kk-badge good'>✓</span>"
                    "<div class='kk-watch-detail'>No alert signals: all patients "
                    "are on a stable or improving trajectory.</div></div>"
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
                        if st.button("Open", key=f"watch_{row.id}", width="stretch"):
                            navigation.open_patient(row.id)
                if len(watch) > 6:
                    if st.button(f"See all {len(watch)} patients needing attention →", key="watch_all"):
                        st.session_state["patients_status_filter"] = ["Needs attention"]
                        navigation.go("patients")
            note("these signals support decision-making and must be interpreted "
                 "in their clinical context.", title="Decision support")

    # --------------------------------------------------------
    # DERNIÈRES SÉANCES
    # --------------------------------------------------------
    section("Latest sessions", "The 10 most recent sessions in the period.")
    recent = current.sort_values("session_date", ascending=False).head(10)
    table = pd.DataFrame({
        "Date": recent["session_date"],
        "Patient": recent["patient_name"],
        "Game": recent["game_name"],
        "Level": recent["level"],
        "Score": recent["score"],
        "Success": recent["success_rate"],
        "Progression": recent["progression"],
        "Left rot. (°)": recent["rotation_left"],
        "Right rot. (°)": recent["rotation_right"],
        "Max abd. (°)": recent["abduction_max"],
        "Max seq.": recent["max_sequence"],
        "Statues (%)": recent["nogo_success_rate"],
        "Pain (/5)": recent["pain_level"],
        "Duration": recent["duration_min"],
    })
    optional = ["Left rot. (°)", "Right rot. (°)", "Max abd. (°)", "Max seq.", "Statues (%)", "Pain (/5)"]
    table = table.drop(columns=[c for c in optional if table[c].isna().all()])
    if any(c in table.columns for c in optional):
        table = table.drop(columns=["Progression"])
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            "Date": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
            "Level": st.column_config.NumberColumn(format="%d"),
            "Score": st.column_config.NumberColumn(format="%.1f"),
            "Success": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100),
            "Progression": st.column_config.NumberColumn(format="%+.1f%%"),
            "Duration": st.column_config.NumberColumn("Duration (min)", format="%.1f"),
            "Left rot. (°)": st.column_config.NumberColumn(format="%d"),
            "Right rot. (°)": st.column_config.NumberColumn(format="%d"),
            "Max abd. (°)": st.column_config.NumberColumn(format="%d"),
            "Max seq.": st.column_config.NumberColumn(format="%d"),
            "Statues (%)": st.column_config.NumberColumn(format="%d"),
            "Pain (/5)": st.column_config.NumberColumn(format="%d"),
        },
    )
