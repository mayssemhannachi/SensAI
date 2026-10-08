import pandas as pd
import streamlit as st

from dashboard import navigation
from dashboard.components import charts
from dashboard.components.ui import (
    alert_badges,
    avatar,
    badge,
    card,
    card_title,
    days_ago,
    delta_chip,
    empty_state,
    esc,
    fmt_date,
    fmt_number,
    insight_card,
    kpi_card,
    kpi_row,
    note,
    render_html,
    section,
    status_badge,
)
from dashboard.utils import analytics, state
from dashboard.utils.api_client import ApiError
from dashboard.utils.data import assign_game, load_dataset, save_patient_diagnosis


def _patient_selector(patients: pd.DataFrame):
    ids = patients["id"].tolist()
    selected = state.selected_patient_id()
    if selected not in ids:
        selected = ids[0]
    labels = patients.set_index("id")
    back_col, select_col = st.columns([1, 4], vertical_alignment="bottom")
    with back_col:
        if st.button("← Tous les patients", width="stretch"):
            navigation.go("patients")
    with select_col:
        chosen = st.selectbox(
            "Patient",
            ids,
            index=ids.index(selected),
            format_func=lambda pid: (
                f"{labels.loc[pid, 'full_name']} · {labels.loc[pid, 'patient_code'] or '#' + str(pid)}"
            ),
            label_visibility="collapsed",
            key=f"patient_select_{selected}",
        )
    if chosen != selected:
        state.select_patient(chosen)
        st.rerun()
    return selected


def _hero(patient: pd.Series, history: pd.DataFrame, status: str, alerts, reference) -> None:
    age = f"{int(patient['age'])} ans" if pd.notna(patient["age"]) else "Âge non renseigné"
    code = patient["patient_code"] or f"#{patient['id']}"
    since = fmt_date(history["session_date"].min()) if not history.empty else "—"
    diagnosis = patient["diagnosis"] or ""
    dx_html = (
        f"<div class='kk-hero-dx'><b>Diagnostic :</b> {esc(diagnosis)}</div>" if diagnosis
        else "<div class='kk-hero-dx'><b>Diagnostic :</b> <i>non renseigné</i></div>"
    )
    render_html(
        f"""
        <div class="kk-hero kk-fade">
          <div class="kk-hero-row">
            {avatar(patient['first_name'], patient['last_name'], seed=patient['id'], large=True)}
            <div style="flex:1;min-width:240px">
              <div class="kk-kicker">Fiche patient</div>
              <div class="kk-hero-name">{esc(patient['full_name'])}</div>
              <div class="kk-hero-meta">
                {badge(code, 'brand')}{badge(age)}
                {badge('Suivi depuis le ' + since, 'neutral') if not history.empty else ''}
                {badge('Dernière séance : ' + days_ago(history['session_date'].max(), reference).lower(), 'neutral') if not history.empty else badge('Aucune séance pour l’instant', 'neutral')}
              </div>
            </div>
            <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px">
              {status_badge(status)}
              <div class="kk-alerts" style="justify-content:flex-end">{alert_badges(alerts)}</div>
            </div>
          </div>
          {dx_html}
        </div>
        """
    )


def _diagnosis_editor(data, patient) -> None:
    label = "Mettre à jour le diagnostic" if patient["diagnosis"] else "Ajouter un diagnostic"
    with st.expander(f"✎ {label}"):
        if not data.is_demo:
            st.caption(
                "Le diagnostic est enregistré comme nouvelle consultation dans le backend. "
                "L’API ne permet pas encore de relire les consultations : le diagnostic "
                "affiché ici est celui saisi pendant cette session."
            )
        else:
            st.caption("Mode démo : la modification est conservée jusqu’à la fermeture du dashboard.")
        with st.form(f"diagnosis_form_{patient['id']}", clear_on_submit=False):
            text = st.text_area("Diagnostic", value=patient["diagnosis"],
                                placeholder="Ex. : trouble développemental de la coordination…")
            submitted = st.form_submit_button("Enregistrer", type="primary")
        if submitted:
            try:
                save_patient_diagnosis(patient["id"], text)
                st.toast("Diagnostic enregistré", icon="✅")
                st.rerun()
            except ValueError as error:
                st.error(str(error))
            except ApiError as error:
                if error.status_code == 401:
                    raise
                st.error(f"Le backend a refusé l’enregistrement : {error}")


def _game_assignment(data, patient) -> None:
    """Associer un jeu au patient (backend) pour que les séances puissent être enregistrées."""
    if data.is_demo or data.games.empty:
        return
    assigned = data.patient_games[data.patient_games["patient_id"] == patient["id"]]
    assigned_ids = set(pd.to_numeric(assigned["game_id"], errors="coerce").dropna().astype(int))
    available = data.games[~data.games["id"].isin(assigned_ids)]
    with st.expander(f"🎮 Jeux assignés ({len(assigned_ids)})"):
        if assigned.empty:
            st.caption("Aucun jeu assigné : le patient ne peut pas encore enregistrer de séance.")
        else:
            render_html(" ".join(badge(name, "brand") for name in assigned["game_name"]))
        if available.empty:
            st.caption("Tous les jeux du catalogue sont déjà assignés.")
            return
        with st.form(f"assign_game_{patient['id']}"):
            game_id = st.selectbox(
                "Assigner un jeu", available["id"].tolist(),
                format_func=lambda gid: data.games.set_index("id").loc[gid, "name"],
            )
            if st.form_submit_button("Assigner", type="primary"):
                try:
                    assign_game(patient["id"], game_id)
                    st.toast("Jeu assigné", icon="✅")
                    st.rerun()
                except ApiError as error:
                    if error.status_code == 401:
                        raise
                    st.error(str(error))


def show_patient_detail():
    data = load_dataset()
    reference = data.reference_date

    if data.patients.empty:
        empty_state("👤", "Aucun patient enregistré", "Créez un profil pour accéder à une fiche.")
        if st.button("＋ Ajouter un patient", type="primary"):
            navigation.go("add_patient")
        return

    patient_id = _patient_selector(data.patients)
    patient = data.patient(patient_id)
    history = data.sessions_of(patient_id)
    alerts = analytics.patient_alerts(history, reference)
    status = analytics.patient_status(history, alerts)

    _hero(patient, history, status, alerts, reference)
    tools_left, tools_right = st.columns(2)
    with tools_left:
        _diagnosis_editor(data, patient)
    with tools_right:
        _game_assignment(data, patient)

    if history.empty:
        st.write("")
        empty_state("🎮", "Aucune séance enregistrée",
                    "Les performances apparaîtront ici dès la première séance de jeu.")
        return

    # --------------------------------------------------------
    # KPI
    # --------------------------------------------------------
    first, last = history.iloc[0], history.iloc[-1]
    recent = history.tail(analytics.TREND_WINDOW)
    level = last["level"]
    section("Situation actuelle", "Dernière séance comparée à la première séance du suivi.")
    kpi_row([
        kpi_card("Séances", fmt_number(len(history)), "▶", "tone-violet",
                 foot=f"{history['game_name'].nunique()} jeu(x) · {fmt_number(history['duration_min'].sum(), 0)} min au total"),
        kpi_card("Dernier score", fmt_number(last["score"], 1), "★", "tone-orange",
                 foot="depuis la 1re séance",
                 delta_html=delta_chip(analytics.delta(last["score"], first["score"]), " pt")),
        kpi_card("Réussite (5 dern.)", fmt_number(recent["success_rate"].mean(), 1), "✓", "tone-green",
                 unit=" %", foot="depuis la 1re séance",
                 delta_html=delta_chip(analytics.delta(last["success_rate"], first["success_rate"]), " pts")),
        kpi_card("Niveau actuel", f"{int(level)}" if pd.notna(level) else "—", "◆", "tone-blue",
                 foot=f"{last['game_name']}"
                 + (f" · départ niveau {int(first['level'])}" if pd.notna(first["level"]) else "")),
    ])

    # --------------------------------------------------------
    # INSIGHTS
    # --------------------------------------------------------
    section("KineKids Intelligence", "Lecture automatique de l’historique — à confronter au jugement clinique.")
    insights = analytics.patient_insights(history, reference)
    columns = st.columns(len(insights), gap="small")
    for column, insight in zip(columns, insights):
        with column:
            render_html(insight_card(insight))

    # --------------------------------------------------------
    # ÉVOLUTION
    # --------------------------------------------------------
    section("Évolution des performances", "Chaque point est une séance, coloré par jeu.")
    colors = charts.game_colors(data.sessions["game_name"])
    with card("patient-evolution"):
        tab_success, tab_score, tab_progress, tab_games = st.tabs(
            ["Réussite", "Score", "Progression", "Par jeu"]
        )
        with tab_success:
            st.plotly_chart(charts.patient_metric_chart(history, "success_rate", colors),
                            config=charts.CHART_CONFIG, key="patient_success")
        with tab_score:
            st.plotly_chart(charts.patient_metric_chart(history, "score", colors),
                            config=charts.CHART_CONFIG, key="patient_score")
        with tab_progress:
            if history["progression"].notna().any():
                st.plotly_chart(charts.progression_chart(history), config=charts.CHART_CONFIG,
                                key="patient_progression")
            else:
                st.info("Pas encore de variation calculable (une seule séance par exercice).")
        with tab_games:
            st.plotly_chart(charts.patient_games_chart(history, colors), config=charts.CHART_CONFIG,
                            key="patient_games")

    # --------------------------------------------------------
    # PREMIÈRE vs DERNIÈRE SÉANCE PAR JEU
    # --------------------------------------------------------
    section("Avant / maintenant, par jeu", "Première et dernière séance de chaque jeu pratiqué.")
    comparison = analytics.first_vs_last(history)
    columns = st.columns(min(3, len(comparison)) or 1, gap="medium")
    for index, row in enumerate(comparison.itertuples(index=False)):
        with columns[index % len(columns)]:
            score_delta = analytics.delta(row.last_score, row.first_score)
            success_delta = analytics.delta(row.last_success, row.first_success)
            level_text = (
                f"Niveau {int(row.first_level)} → {int(row.last_level)}"
                if pd.notna(row.first_level) and pd.notna(row.last_level) else "Niveau n.c."
            )
            color = colors.get(row.game_name, "#5B5BD6")
            render_html(
                f"""
                <div class="kk-kpi" style="min-height:0">
                  <div class="kk-kpi-top">
                    <span style="width:10px;height:10px;border-radius:3px;background:{color}"></span>
                    <div class="kk-card-title">{esc(row.game_name)}</div>
                    <span style="margin-left:auto">{badge(f'{row.sessions} séance(s)')}</span>
                  </div>
                  <div class="kk-pcard-stats" style="grid-template-columns:repeat(2,1fr)">
                    <div class="kk-stat"><div class="kk-stat-label">Réussite</div>
                      <div class="kk-stat-value">{fmt_number(row.first_success)} → {fmt_number(row.last_success, suffix=' %')}</div>
                      {delta_chip(success_delta, ' pts')}</div>
                    <div class="kk-stat"><div class="kk-stat-label">Score</div>
                      <div class="kk-stat-value">{fmt_number(row.first_score)} → {fmt_number(row.last_score)}</div>
                      {delta_chip(score_delta, ' pt')}</div>
                  </div>
                  <div class="kk-kpi-foot">{level_text}</div>
                </div>
                """
            )

    # --------------------------------------------------------
    # HISTORIQUE
    # --------------------------------------------------------
    section("Historique des séances", f"{len(history)} séance(s), de la plus récente à la plus ancienne.")
    table = history.sort_values("session_date", ascending=False)
    display = pd.DataFrame({
        "Date": table["session_date"],
        "Jeu": table["game_name"],
        "Exercice": table["exercise_name"],
        "Niveau": table["level"],
        "Score": table["score"],
        "Réussite": table["success_rate"],
        "Répétitions": table["repetitions"],
        "Durée (min)": table["duration_min"],
        "Progression": table["progression"],
    })
    st.dataframe(
        display,
        hide_index=True,
        width="stretch",
        height=min(420, 38 * len(display) + 40),
        column_config={
            "Date": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
            "Niveau": st.column_config.NumberColumn(format="%d"),
            "Score": st.column_config.NumberColumn(format="%.1f"),
            "Réussite": st.column_config.ProgressColumn(format="%.0f %%", min_value=0, max_value=100),
            "Répétitions": st.column_config.NumberColumn(format="%d"),
            "Durée (min)": st.column_config.NumberColumn(format="%.1f"),
            "Progression": st.column_config.NumberColumn(format="%+.1f %%"),
        },
    )
    st.download_button(
        "⤓ Exporter l’historique (CSV)",
        display.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"kinekids_{patient['patient_code'] or patient['id']}_seances.csv",
        mime="text/csv",
    )
    note("la « progression » est la variation du score par rapport à la séance précédente "
         "du même exercice.", title="Définition")
