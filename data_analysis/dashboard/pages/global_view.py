import pandas as pd
import streamlit as st

from dashboard.components.charts import (
    game_performance_chart,
    global_progression_chart,
    global_score_evolution_chart,
    success_distribution_chart,
)
from dashboard.components.kpi_cards import display_kpi_row
from dashboard.utils.data import load_session_analysis


def page_header(last_session_date):

    st.markdown(
        f"""
        <div class="page-header animate">
            <div class="page-kicker">ESPACE THÉRAPEUTE · SUIVI PÉDIATRIQUE</div>
            <div class="page-title">Vue d’ensemble</div>
            <div class="page-description">
                Les indicateurs clés et les séances récentes de vos patients.
            </div>
            <div class="page-meta">Données jusqu’au {last_session_date:%d/%m/%Y}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_global_view():

    df = load_session_analysis()

    if df.empty:

        st.warning(
            "Aucune donnée de séance disponible."
        )

        return

    valid_dates = df["session_date"].dropna()
    if valid_dates.empty:
        st.info("Les séances reçues ne contiennent pas de date exploitable.")
        return

    latest_data_date = valid_dates.max().normalize()
    page_header(latest_data_date)

    period_options = {
        "30 derniers jours": 30,
        "90 derniers jours": 90,
        "Tout l’historique": None,
    }
    filter_column, period_note = st.columns([1, 2.5], vertical_alignment="center")
    with filter_column:
        selected_period = st.selectbox(
            "Période d’analyse",
            list(period_options),
            index=1,
            key="global_analysis_period",
        )

    period_days = period_options[selected_period]
    if period_days is not None:
        period_start = latest_data_date - pd.Timedelta(days=period_days - 1)
        df = df[df["session_date"] >= period_start].copy()
    else:
        period_start = df["session_date"].min().normalize()

    if df.empty:
        st.info("Aucune séance enregistrée pour cette période.")
        return

    with period_note:
        st.caption(
            f"Du {period_start:%d/%m/%Y} au {latest_data_date:%d/%m/%Y} "
            f"· {df['id_session'].nunique()} séances"
        )

    # ======================================================
    # KPI
    # ======================================================

    patient_count = df["patient_id"].nunique()

    session_count = df["id_session"].nunique()

    mean_success = df["success_rate"].mean()

    mean_progression = df["progression"].mean()

    display_kpi_row(
        [
            {
                "title": "Patients actifs",
                "value": patient_count,
                "description": f"Sur {selected_period.lower()}",
            },
            {
                "title": "Séances réalisées",
                "value": session_count,
                "description": f"Sur {selected_period.lower()}",
            },
            {
                "title": "Réussite moyenne",
                "value": f"{mean_success:.1f}%" if pd.notna(mean_success) else "—",
                "description": f"Moyenne · {selected_period.lower()}",
            },
            {
                "title": "Progression moyenne",
                "value": (
                    f"{mean_progression:+.1f}%"
                    if pd.notna(mean_progression)
                    else "—"
                ),
                "description": f"Moyenne · {selected_period.lower()}",
            },
        ]
    )

    st.markdown("### La progression en un coup d’œil")
    st.caption("Les tendances globales de rééducation")

    # ======================================================
    # SCORE EVOLUTION
    # ======================================================

    daily_data = df.dropna(subset=["session_date"]).copy()
    daily_data["session_date"] = daily_data["session_date"].dt.normalize()
    daily_score = (
        daily_data.groupby("session_date", as_index=False)
        .agg(mean_score=("score", "mean"))
        .sort_values("session_date")
    )

    if not daily_score.empty:

        daily_score["session_date"] = pd.to_datetime(
            daily_score["session_date"]
        )

        col1, col2 = st.columns(
            [1.65, 1],
            gap="large",
        )

        with col1, st.container():
            st.markdown("**Évolution du score moyen**")

            fig = global_score_evolution_chart(daily_score)

            st.plotly_chart(
                fig,
                width="stretch",
                config={"displayModeBar": False},
            )

        # ==================================================
        # SUCCESS DISTRIBUTION
        # ==================================================

        bins = [
            float("-inf"),
            40,
            50,
            60,
            70,
            80,
            float("inf"),
        ]

        labels = [
            "< 40%",
            "40–50%",
            "50–60%",
            "60–70%",
            "70–80%",
            "80%+",
        ]

        temp = df.copy()

        temp["success_range"] = pd.cut(
            temp["success_rate"],
            bins=bins,
            labels=labels,
            include_lowest=True,
        )

        distribution = (
            temp["success_range"]
            .value_counts()
            .reindex(labels)
            .fillna(0)
            .reset_index()
        )

        distribution.columns = [
            "range",
            "count",
        ]

        with col2, st.container():
            st.markdown("**Répartition des performances**")

            fig = success_distribution_chart(distribution)

            st.plotly_chart(
                fig,
                width="stretch",
                config={"displayModeBar": False},
            )

    # ======================================================
    # GAMES
    # ======================================================

    st.markdown("### Les jeux KineKids")

    game_data = (
        df.groupby(
            "name_game",
            as_index=False,
        )
        .agg(
            mean_success_rate=(
                "success_rate",
                "mean",
            )
        )
        .sort_values(
            "mean_success_rate",
            ascending=False,
        )
    )

    col1, col2 = st.columns(
        [1.2, 1],
        gap="large",
    )

    with col1, st.container():
        st.markdown("**Performance moyenne par jeu**")

        fig = game_performance_chart(game_data)

        st.plotly_chart(
            fig,
            width="stretch",
            config={"displayModeBar": False},
        )

    # ======================================================
    # ATTENTION PATIENTS
    # ======================================================

    latest = (
        df.dropna(subset=["session_date"])
        .sort_values("session_date")
        .groupby(
            "patient_id",
            as_index=False,
        )
        .tail(1)
        .copy()
    )

    attention = latest[
        (latest["progression"] < 0)
        | (latest["success_rate"] < 40)
    ].copy()

    with col2, st.container():
        st.markdown("**Séances à revoir**")
        st.caption(
            "Signal automatique si réussite < 40 % ou progression négative ; "
            "à interpréter dans le contexte clinique."
        )

        if attention.empty:
            st.success("Aucun signal à revoir sur la période sélectionnée.")
        else:
            for _, row in attention.head(6).iterrows():
                with st.container(border=True):
                    name_column, metric_column, action_column = st.columns(
                        [1.6, 1.4, 0.8],
                        vertical_alignment="center",
                    )
                    with name_column:
                        st.markdown(
                            f"**{row['first_name']} {row['last_name']}**"
                        )
                        st.caption(f"Séance du {row['session_date']:%d/%m/%Y}")
                    with metric_column:
                        st.caption(f"Réussite · {row['success_rate']:.1f}%")
                        if pd.notna(row["progression"]):
                            st.caption(f"Progression · {row['progression']:+.1f}%")
                        else:
                            st.caption("Progression · non calculée")
                    with action_column:
                        if st.button(
                            "Ouvrir",
                            key=f"open_attention_patient_{row['patient_id']}",
                            width="stretch",
                        ):
                            st.session_state["selected_patient_id"] = row["patient_id"]
                            st.session_state["page"] = "Fiche patient"
                            st.rerun()

    # ======================================================
    # PROGRESSION
    # ======================================================

    st.markdown("### Évolution globale")

    progression_data = (
        daily_data.groupby("session_date", as_index=False)
        .agg(mean_progression=("progression", "mean"))
        .sort_values("session_date")
    )

    if not progression_data.empty:

        progression_data["session_date"] = pd.to_datetime(
            progression_data["session_date"]
        )

        fig = global_progression_chart(progression_data)

        st.plotly_chart(
            fig,
            width="stretch",
            config={"displayModeBar": False},
        )

    # ======================================================
    # DERNIÈRES SÉANCES
    # ======================================================

    st.markdown("### Dernières séances")

    recent = (
        df.sort_values(
            "session_date",
            ascending=False,
        )
        .head(8)
        .copy()
    )

    if recent.empty:
        st.info("Aucune séance récente à afficher.")
    else:
        recent["Date"] = recent["session_date"].dt.strftime("%d/%m/%Y")
        recent_display = recent[
            [
                "Date",
                "first_name",
                "last_name",
                "name_game",
                "score",
                "success_rate",
                "progression",
            ]
        ].copy()
        recent_display["Patient"] = (
            recent_display["first_name"]
            + " "
            + recent_display["last_name"]
        )
        recent_display = recent_display[
            [
                "Date",
                "Patient",
                "name_game",
                "score",
                "success_rate",
                "progression",
            ]
        ]
        recent_display.columns = [
            "Date",
            "Patient",
            "Jeu",
            "Score",
            "Réussite (%)",
            "Progression (%)",
        ]

        st.caption(f"Les {len(recent_display)} séances les plus récentes")
        st.dataframe(
            recent_display,
            width="stretch",
            height=360,
            hide_index=True,
            column_config={
                "Score": st.column_config.NumberColumn(format="%.1f"),
                "Réussite (%)": st.column_config.NumberColumn(format="%.1f%%"),
                "Progression (%)": st.column_config.NumberColumn(format="%+.1f%%"),
            },
        )