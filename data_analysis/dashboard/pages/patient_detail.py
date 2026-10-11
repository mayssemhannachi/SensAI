import pandas as pd
import streamlit as st

from dashboard import navigation
from dashboard.components import charts, game_settings
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
from dashboard.utils.data import (
    assign_game,
    playable_games,
    create_activation_code,
    load_dataset,
    save_patient_diagnosis,
    update_game_settings,
)


def _patient_selector(patients: pd.DataFrame):
    ids = patients["id"].tolist()
    selected = state.selected_patient_id()
    if selected not in ids:
        selected = ids[0]
    labels = patients.set_index("id")
    back_col, select_col = st.columns([1, 4], vertical_alignment="bottom")
    with back_col:
        if st.button("← All patients", width="stretch"):
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
    age = f"{int(patient['age'])} years old" if pd.notna(patient["age"]) else "Age not provided"
    code = patient["patient_code"] or f"#{patient['id']}"
    since = fmt_date(history["session_date"].min()) if not history.empty else "—"
    diagnosis = patient["diagnosis"] or ""
    dx_html = (
        f"<div class='kk-hero-dx'><b>Diagnosis:</b> {esc(diagnosis)}</div>" if diagnosis
        else "<div class='kk-hero-dx'><b>Diagnosis:</b> <i>not provided</i></div>"
    )
    render_html(
        f"""
        <div class="kk-hero kk-fade">
          <div class="kk-hero-row">
            {avatar(patient['first_name'], patient['last_name'], seed=patient['id'], large=True)}
            <div style="flex:1;min-width:240px">
              <div class="kk-kicker">Patient record</div>
              <div class="kk-hero-name">{esc(patient['full_name'])}</div>
              <div class="kk-hero-meta">
                {badge(code, 'brand')}{badge(age)}
                {(badge('Patient account activated', 'good', '✓') if patient.get('has_account') else badge('Patient account not activated', 'warning', '!')) if 'has_account' in patient.index else ''}
                {badge('Followed since ' + since, 'neutral') if not history.empty else ''}
                {badge('Last session: ' + days_ago(history['session_date'].max(), reference).lower(), 'neutral') if not history.empty else badge('No sessions yet', 'neutral')}
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
    label = "Update diagnosis" if patient["diagnosis"] else "Add a diagnosis"
    with st.expander(f"✎ {label}"):
        if data.is_demo:
            st.caption("Demo mode: the change is kept until the dashboard is closed.")
        elif data.diagnosis_readable:
            st.caption("The diagnosis is saved as a new consultation in the backend.")
        else:
            st.caption(
                "The diagnosis is saved as a new consultation. This backend version cannot "
                "read consultations back: only the diagnosis entered during this session "
                "is shown."
            )
        with st.form(f"diagnosis_form_{patient['id']}", clear_on_submit=False):
            text = st.text_area("Diagnosis", value=patient["diagnosis"],
                                placeholder="e.g. developmental coordination disorder…")
            submitted = st.form_submit_button("Save", type="primary")
        if submitted:
            try:
                save_patient_diagnosis(patient["id"], text)
                st.toast("Diagnosis saved", icon="✅")
                st.rerun()
            except ValueError as error:
                st.error(str(error))
            except ApiError as error:
                if error.status_code == 401:
                    raise
                st.error(f"The backend rejected the save: {error}")


def _settings_form(key: str, slug: str | None, current: dict) -> dict | None:
    """Formulaire des réglages d'un jeu ; renvoie la configuration si validé."""
    with st.form(key):
        config = game_settings.settings_fields(slug, current, key)
        active = st.toggle("Game visible to the patient", value=bool((current or {}).get("active", True)),
                           key=f"{key}_active")
        if st.form_submit_button("Save settings", type="primary"):
            problem = game_settings.validate(slug, config)
            if problem:
                st.error(problem)
                return None
            return {**config, "active": bool(active)}
    return None


def _game_assignment(data, patient) -> None:
    """Jeux assignés au patient, leurs réglages, et code d'activation (mode Backend)."""
    if data.is_demo:
        return
    assigned = data.patient_games[data.patient_games["patient_id"] == patient["id"]]
    with st.expander(f"🎮 Games and settings ({len(assigned)})"):
        st.caption("Visible games appear in the patient's space on the website, "
                   "with these settings.")
        for row in assigned.itertuples(index=False):
            config = row.configuration if isinstance(row.configuration, dict) else {}
            state_label = "visible" if config.get("active", True) else "hidden"
            st.markdown(f"**{row.game_name}** · {state_label}")
            updated = _settings_form(f"settings_{row.patient_game_id}", getattr(row, "game_slug", None), config)
            if updated is not None:
                try:
                    update_game_settings(row.patient_game_id, updated)
                    st.toast("Settings saved", icon="✅")
                    st.rerun()
                except ApiError as error:
                    if error.status_code == 401:
                        raise
                    st.error(str(error))

        assigned_ids = set(pd.to_numeric(assigned["game_id"], errors="coerce").dropna().astype(int))
        available = playable_games(data.games)
        available = available[~available["id"].isin(assigned_ids)]
        if not available.empty:
            st.markdown("**Assign a new game**")
            game_id = st.selectbox(
                "Game", available["id"].tolist(), key=f"new_game_{patient['id']}",
                format_func=lambda gid: data.games.set_index("id").loc[gid, "name"],
            )
            slug = data.games.set_index("id").loc[game_id, "slug"]
            st.caption(game_settings.GAME_HINTS.get(slug, ""))
            config = _settings_form(f"assign_game_{patient['id']}_{slug}", slug, None)
            if config is not None:
                try:
                    assign_game(patient["id"], game_id, config)
                    st.toast("Game assigned", icon="✅")
                    st.rerun()
                except ApiError as error:
                    if error.status_code == 401:
                        raise
                    st.error(str(error))

    with st.expander("🔑 Patient account activation code"):
        st.caption("The patient (or their parent) enters this code on the “Activate my account” page "
                   "of the website to create their login. Valid for 30 days, single use.")
        code_key = f"activation_code_{patient['id']}"
        if st.button("Generate a code", key=f"gen_code_{patient['id']}"):
            try:
                st.session_state[code_key] = create_activation_code(patient["id"])["code"]
            except ApiError as error:
                if error.status_code == 401:
                    raise
                st.error(str(error))
        if st.session_state.get(code_key):
            st.code(st.session_state[code_key], language=None)


def show_patient_detail():
    data = load_dataset()
    reference = data.reference_date

    if data.patients.empty:
        empty_state("👤", "No patients registered", "Create a profile to open a patient record.")
        if st.button("＋ Add a patient", type="primary"):
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
        empty_state("🎮", "No sessions recorded",
                    "Performance will appear here after the first game session.")
        return

    # --------------------------------------------------------
    # KPI
    # --------------------------------------------------------
    first, last = history.iloc[0], history.iloc[-1]
    recent = history.tail(analytics.TREND_WINDOW)
    level = last["level"]
    section("Current status", "Latest session compared with the first session of follow-up.")
    kpi_row([
        kpi_card("Sessions", fmt_number(len(history)), "▶", "tone-violet",
                 foot=f"{history['game_name'].nunique()} game(s) · {fmt_number(history['duration_min'].sum(), 0)} min in total"),
        kpi_card("Latest score", fmt_number(last["score"], 1), "★", "tone-orange",
                 foot="since 1st session",
                 delta_html=delta_chip(analytics.delta(last["score"], first["score"]), " pt")),
        kpi_card("Success (last 5)", fmt_number(recent["success_rate"].mean(), 1), "✓", "tone-green",
                 unit="%", foot="since 1st session",
                 delta_html=delta_chip(analytics.delta(last["success_rate"], first["success_rate"]), " pts")),
        kpi_card("Current level", f"{int(level)}" if pd.notna(level) else "—", "◆", "tone-blue",
                 foot=f"{last['game_name']}"
                 + (f" · started at level {int(first['level'])}" if pd.notna(first["level"]) else "")),
    ])

    # --------------------------------------------------------
    # INSIGHTS
    # --------------------------------------------------------
    section("SensAI Intelligence", "Automated reading of the history — to be weighed against clinical judgment.")
    insights = analytics.patient_insights(history, reference)
    per_row = 3 if len(insights) > 4 else max(len(insights), 1)
    for start in range(0, len(insights), per_row):
        columns = st.columns(per_row, gap="small")
        for column, insight in zip(columns, insights[start:start + per_row]):
            with column:
                render_html(insight_card(insight))

    # --------------------------------------------------------
    # AMPLITUDE & AUTO-ÉVALUATION (Le Hibou)
    # --------------------------------------------------------
    rotation = history.dropna(subset=["rotation_left", "rotation_right"], how="all")
    if not rotation.empty:
        last_rot = rotation.iloc[-1]
        first_rot = rotation.iloc[0]
        left, right = last_rot["rotation_left"], last_rot["rotation_right"]
        target = last_rot["target_angle"]
        sym = analytics.symmetry(left, right)
        section("Cervical range of motion & symmetry",
                "Maximum rotation reached in each The Owl session, compared with the prescribed target angle.")
        target_text = f"target {fmt_number(target)}°" if pd.notna(target) else "target n/a"
        kpi_row([
            kpi_card("Left rotation", fmt_number(left), "←", "tone-violet", unit="°", foot=target_text,
                     delta_html=delta_chip(analytics.delta(left, first_rot["rotation_left"]), "°", 0)),
            kpi_card("Right rotation", fmt_number(right), "→", "tone-blue", unit="°", foot=target_text,
                     delta_html=delta_chip(analytics.delta(right, first_rot["rotation_right"]), "°", 0)),
            kpi_card("Symmetry", fmt_number(sym), "⇄", "tone-green", unit="%",
                     foot="symmetric" if sym >= 80 else "asymmetry to monitor"),
            kpi_card("Average hold", fmt_number(last_rot["hold_seconds_avg"], 1), "⏱", "tone-orange", unit=" s",
                     foot=f"smoothness {fmt_number(last_rot['smoothness'])}/100"
                     if pd.notna(last_rot["smoothness"]) else "last session"),
        ])
        st.write("")
        left_col, right_col = st.columns([1.5, 1], gap="medium")
        with left_col:
            with card("amplitude"):
                card_title("Range of motion over time", "Degrees reached left and right, and target angle.")
                st.plotly_chart(charts.amplitude_chart(history), config=charts.CHART_CONFIG, key="patient_amplitude")
        with right_col:
            with card("pain"):
                card_title("Pain & effort", "Child's self-assessment after each session (0 to 5).")
                if history[["pain_level", "effort"]].notna().any().any():
                    st.plotly_chart(charts.pain_effort_chart(history), config=charts.CHART_CONFIG, key="patient_pain")
                else:
                    st.info("No self-assessment yet.")

    # --------------------------------------------------------
    # ABDUCTION DE L'ÉPAULE (Le Gardien des Lucioles)
    # --------------------------------------------------------
    abduction = history.dropna(subset=["abduction_max"])
    if not abduction.empty:
        last_abd, first_abd = abduction.iloc[-1], abduction.iloc[0]
        threshold = last_abd["target_angle"]
        arm = {"R": "right arm", "L": "left arm", "BI": "both arms", "both": "both arms"}.get(
            last_abd["affected_arm"], "trained arm")
        recent_comp = abduction.tail(3)["compensations"].mean()
        section("Arm elevation (shoulder)",
                f"Elevation ({arm}) in each Firefly Guardian session, compared with the prescribed height.")
        kpi_row([
            kpi_card("Max abduction", fmt_number(last_abd["abduction_max"]), "↑", "tone-violet", unit="°",
                     foot=f"threshold {fmt_number(threshold)}°" if pd.notna(threshold) else "last session",
                     delta_html=delta_chip(analytics.delta(last_abd["abduction_max"], first_abd["abduction_max"]), "°", 0)),
            kpi_card("Mean peak", fmt_number(last_abd["abduction_mean_peak"]), "◠", "tone-blue", unit="°",
                     foot="average of validated repetitions",
                     delta_html=delta_chip(analytics.delta(last_abd["abduction_mean_peak"],
                                                           first_abd["abduction_mean_peak"]), "°", 0)),
            kpi_card("Compensations", fmt_number(recent_comp, 1), "⚠", "tone-orange",
                     foot="average of the last 3 sessions"
                     if pd.notna(recent_comp) else "not measured"),
            kpi_card("Fireflies", fmt_number(last_abd["repetitions"]), "✨", "tone-green",
                     foot="brought back in the last session"),
        ])
        st.write("")
        abd_col, comp_col = st.columns([1.5, 1], gap="medium")
        with abd_col:
            with card("abduction"):
                card_title("Abduction over time", "Maximum range and mean peak, with the prescribed threshold.")
                st.plotly_chart(charts.abduction_chart(abduction), config=charts.CHART_CONFIG,
                                key="patient_abduction")
        with comp_col:
            with card("compensations"):
                card_title("Compensations", "Times the other arm was raised during the session.")
                st.plotly_chart(charts.compensation_chart(abduction), config=charts.CHART_CONFIG,
                                key="patient_compensations")
        if rotation.empty and history[["pain_level", "effort"]].notna().any().any():
            with card("pain-lucioles"):
                card_title("Pain & effort", "Child's self-assessment after each session (0 to 5).")
                st.plotly_chart(charts.pain_effort_chart(history), config=charts.CHART_CONFIG,
                                key="patient_pain_lucioles")

    # --------------------------------------------------------
    # MÉMOIRE ET COORDINATION (La Danse des Lucioles, ergothérapie)
    # --------------------------------------------------------
    sequence = history.dropna(subset=["max_sequence"])
    if not sequence.empty:
        last_seq, first_seq = sequence.iloc[-1], sequence.iloc[0]
        recent = sequence.tail(3)
        section("Memory and coordination",
                "Flower sequences reproduced with the hands in each Firefly Dance session.")
        kpi_row([
            kpi_card("Longest sequence", fmt_number(last_seq["max_sequence"]), "✿", "tone-violet",
                     unit=" flowers", foot=f"best {fmt_number(sequence['max_sequence'].max())} flowers",
                     delta_html=delta_chip(analytics.delta(last_seq["max_sequence"], first_seq["max_sequence"]), "", 0)),
            kpi_card("Order errors", fmt_number(recent["sequence_errors"].mean(), 1), "✗", "tone-orange",
                     foot="average of the last 3 sessions"),
            kpi_card("Hints from Léo", fmt_number(recent["hints_used"].mean(), 1), "?", "tone-blue",
                     foot="average of the last 3 sessions"),
            kpi_card("Time per flower", fmt_number(last_seq["mean_step_sec"], 1), "⏱", "tone-green", unit=" s",
                     foot="movement planning speed"),
        ])
        st.write("")
        seq_col, err_col = st.columns([1.5, 1], gap="medium")
        with seq_col:
            with card("sequence"):
                card_title("Sequence length", "Longest successful dance in each session (working memory).")
                st.plotly_chart(charts.sequence_chart(sequence), config=charts.CHART_CONFIG, key="patient_sequence")
        with err_col:
            with card("seq-errors"):
                card_title("Errors and hints", "Flowers touched in the wrong order and hints given by Léo.")
                st.plotly_chart(charts.errors_hints_chart(sequence), config=charts.CHART_CONFIG,
                                key="patient_seq_errors")
        if rotation.empty and abduction.empty and history[["pain_level", "effort"]].notna().any().any():
            with card("pain-danse"):
                card_title("Pain & effort", "Child's self-assessment after each session (0 to 5).")
                st.plotly_chart(charts.pain_effort_chart(history), config=charts.CHART_CONFIG,
                                key="patient_pain_danse")

    # --------------------------------------------------------
    # ATTENTION ET CONTRÔLE DES GESTES (Le Gardien du Château, ergothérapie)
    # --------------------------------------------------------
    castle = history.dropna(subset=["nogo_success_rate"])
    if not castle.empty:
        last_c, first_c = castle.iloc[-1], castle.iloc[0]
        section("Attention and movement control",
                "Challenges done at the right time and statues held in front of the ogre, in each Guardian of the Castle game.")
        fade = last_c.get("accuracy_start") - last_c.get("accuracy_end") \
            if pd.notna(last_c.get("accuracy_start")) and pd.notna(last_c.get("accuracy_end")) else None
        kpi_row([
            kpi_card("Challenges completed", fmt_number(last_c["go_success_rate"]), "✦", "tone-blue", unit="%",
                     foot="attention: right movement at the right time",
                     delta_html=delta_chip(analytics.delta(last_c["go_success_rate"], first_c["go_success_rate"]), "", 0)),
            kpi_card("Statues held", fmt_number(last_c["nogo_success_rate"]), "♜", "tone-violet", unit="%",
                     foot="impulse control in front of the ogre",
                     delta_html=delta_chip(analytics.delta(last_c["nogo_success_rate"], first_c["nogo_success_rate"]), "", 0)),
            kpi_card("Reaction time", fmt_number(last_c["rt_mean_ms"]), "⏱", "tone-green", unit=" ms",
                     foot=f"variability ± {fmt_number(last_c['rt_sd_ms'])} ms"),
            kpi_card("End of game", fmt_number(last_c["accuracy_end"]), "◔", "tone-orange", unit="%",
                     foot=(f"{fmt_number(fade)} points lower than at the start" if fade is not None and fade > 0
                           else "success maintained to the end")),
        ])
        st.write("")
        att_col, castle_err_col = st.columns([1.5, 1], gap="medium")
        with att_col:
            with card("attention"):
                card_title("Attention and inhibition", "Challenges completed and statues held in front of the ogre, per session.")
                st.plotly_chart(charts.attention_chart(castle), config=charts.CHART_CONFIG, key="patient_attention")
        with castle_err_col:
            with card("castle-errors"):
                card_title("Error types", "Moving in front of the ogre (impulsivity), missing a challenge, wrong movement.")
                st.plotly_chart(charts.castle_errors_chart(castle), config=charts.CHART_CONFIG,
                                key="patient_castle_errors")

    # --------------------------------------------------------
    # ÉVOLUTION
    # --------------------------------------------------------
    section("Performance over time", "Each point is a session, colored by game.")
    colors = charts.game_colors(data.sessions["game_name"])
    with card("patient-evolution"):
        tab_success, tab_score, tab_progress, tab_games = st.tabs(
            ["Success", "Score", "Progression", "By game"]
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
                st.info("No change can be calculated yet (only one session per exercise).")
        with tab_games:
            st.plotly_chart(charts.patient_games_chart(history, colors), config=charts.CHART_CONFIG,
                            key="patient_games")

    # --------------------------------------------------------
    # PREMIÈRE vs DERNIÈRE SÉANCE PAR JEU
    # --------------------------------------------------------
    section("Before / now, by game", "First and last session of each game played.")
    comparison = analytics.first_vs_last(history)
    columns = st.columns(min(3, len(comparison)) or 1, gap="medium")
    for index, row in enumerate(comparison.itertuples(index=False)):
        with columns[index % len(columns)]:
            score_delta = analytics.delta(row.last_score, row.first_score)
            success_delta = analytics.delta(row.last_success, row.first_success)
            level_text = (
                f"Level {int(row.first_level)} → {int(row.last_level)}"
                if pd.notna(row.first_level) and pd.notna(row.last_level) else "Level n/a"
            )
            color = colors.get(row.game_name, "#5B5BD6")
            render_html(
                f"""
                <div class="kk-kpi" style="min-height:0">
                  <div class="kk-kpi-top">
                    <span style="width:10px;height:10px;border-radius:3px;background:{color}"></span>
                    <div class="kk-card-title">{esc(row.game_name)}</div>
                    <span style="margin-left:auto">{badge(f'{row.sessions} session(s)')}</span>
                  </div>
                  <div class="kk-pcard-stats" style="grid-template-columns:repeat(2,1fr)">
                    <div class="kk-stat"><div class="kk-stat-label">Success</div>
                      <div class="kk-stat-value">{fmt_number(row.first_success)} → {fmt_number(row.last_success, suffix='%')}</div>
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
    section("Session history", f"{len(history)} session(s), most recent first.")
    table = history.sort_values("session_date", ascending=False)
    display = pd.DataFrame({
        "Date": table["session_date"],
        "Game": table["game_name"],
        "Exercise": table["exercise_name"],
        "Level": table["level"],
        "Score": table["score"],
        "Success": table["success_rate"],
        "Repetitions": table["repetitions"],
        "Duration (min)": table["duration_min"],
        "Progression": table["progression"],
    })
    extra = {
        "Left rot. (°)": "rotation_left",
        "Right rot. (°)": "rotation_right",
        "Max abduction (°)": "abduction_max",
        "Compensations": "compensations",
        "Max sequence": "max_sequence",
        "Order errors": "sequence_errors",
        "Statues (%)": "nogo_success_rate",
        "Reaction (ms)": "rt_mean_ms",
        "Pain (/5)": "pain_level",
        "Effort (/5)": "effort",
    }
    for label, column in extra.items():
        if table[column].notna().any():
            display[label] = table[column].to_numpy()
    if display["Exercise"].nunique(dropna=True) <= 1:
        display = display.drop(columns="Exercise")
    if display["Progression"].isna().all() or {"Left rot. (°)", "Max abduction (°)", "Max sequence", "Statues (%)"} & set(display.columns):
        display = display.drop(columns="Progression")
    st.dataframe(
        display,
        hide_index=True,
        width="stretch",
        height=min(420, 38 * len(display) + 40),
        column_config={
            "Date": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
            "Level": st.column_config.NumberColumn(format="%d"),
            "Score": st.column_config.NumberColumn(format="%.1f"),
            "Success": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100),
            "Repetitions": st.column_config.NumberColumn(format="%d"),
            "Duration (min)": st.column_config.NumberColumn(format="%.1f"),
            "Progression": st.column_config.NumberColumn(format="%+.1f%%"),
            "Left rot. (°)": st.column_config.NumberColumn(format="%d"),
            "Right rot. (°)": st.column_config.NumberColumn(format="%d"),
            "Max abduction (°)": st.column_config.NumberColumn(format="%d"),
            "Compensations": st.column_config.NumberColumn(format="%d"),
            "Max sequence": st.column_config.NumberColumn(format="%d"),
            "Order errors": st.column_config.NumberColumn(format="%d"),
            "Pain (/5)": st.column_config.NumberColumn(format="%d"),
            "Effort (/5)": st.column_config.NumberColumn(format="%d"),
        },
    )
    st.download_button(
        "⤓ Export history (CSV)",
        display.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"sensai_{patient['patient_code'] or patient['id']}_sessions.csv",
        mime="text/csv",
    )
    note("“progression” is the change in score compared with the previous session "
         "of the same exercise.", title="Definition")
