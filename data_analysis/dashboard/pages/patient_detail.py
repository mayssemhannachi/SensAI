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
                {(badge('Compte patient activé', 'good', '✓') if patient.get('has_account') else badge('Compte patient non activé', 'warning', '!')) if 'has_account' in patient.index else ''}
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
        if data.is_demo:
            st.caption("Mode démo : la modification est conservée jusqu’à la fermeture du dashboard.")
        elif data.diagnosis_readable:
            st.caption("Le diagnostic est enregistré comme nouvelle consultation dans le backend.")
        else:
            st.caption(
                "Le diagnostic est enregistré comme nouvelle consultation. Cette version du "
                "backend ne permet pas de relire les consultations : seul le diagnostic saisi "
                "pendant cette session est affiché."
            )
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


def _settings_form(key: str, slug: str | None, current: dict) -> dict | None:
    """Formulaire des réglages d'un jeu ; renvoie la configuration si validé."""
    with st.form(key):
        config = game_settings.settings_fields(slug, current, key)
        active = st.toggle("Jeu visible pour le patient", value=bool((current or {}).get("active", True)),
                           key=f"{key}_active")
        if st.form_submit_button("Enregistrer les réglages", type="primary"):
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
    with st.expander(f"🎮 Jeux et réglages ({len(assigned)})"):
        st.caption("Les jeux visibles apparaissent dans l’espace du patient sur le site, "
                   "avec ces réglages.")
        for row in assigned.itertuples(index=False):
            config = row.configuration if isinstance(row.configuration, dict) else {}
            state_label = "visible" if config.get("active", True) else "masqué"
            st.markdown(f"**{row.game_name}** · {state_label}")
            updated = _settings_form(f"settings_{row.patient_game_id}", getattr(row, "game_slug", None), config)
            if updated is not None:
                try:
                    update_game_settings(row.patient_game_id, updated)
                    st.toast("Réglages enregistrés", icon="✅")
                    st.rerun()
                except ApiError as error:
                    if error.status_code == 401:
                        raise
                    st.error(str(error))

        assigned_ids = set(pd.to_numeric(assigned["game_id"], errors="coerce").dropna().astype(int))
        available = playable_games(data.games)
        available = available[~available["id"].isin(assigned_ids)]
        if not available.empty:
            st.markdown("**Assigner un nouveau jeu**")
            game_id = st.selectbox(
                "Jeu", available["id"].tolist(), key=f"new_game_{patient['id']}",
                format_func=lambda gid: data.games.set_index("id").loc[gid, "name"],
            )
            slug = data.games.set_index("id").loc[game_id, "slug"]
            st.caption(game_settings.GAME_HINTS.get(slug, ""))
            config = _settings_form(f"assign_game_{patient['id']}_{slug}", slug, None)
            if config is not None:
                try:
                    assign_game(patient["id"], game_id, config)
                    st.toast("Jeu assigné", icon="✅")
                    st.rerun()
                except ApiError as error:
                    if error.status_code == 401:
                        raise
                    st.error(str(error))

    with st.expander("🔑 Code d’activation du compte patient"):
        st.caption("Le patient (ou son parent) saisit ce code sur la page « Activer mon compte » "
                   "du site pour créer ses identifiants. Valable 30 jours, utilisable une fois.")
        code_key = f"activation_code_{patient['id']}"
        if st.button("Générer un code", key=f"gen_code_{patient['id']}"):
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
    section("SensAI Intelligence", "Lecture automatique de l’historique — à confronter au jugement clinique.")
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
        section("Amplitude cervicale & symétrie",
                "Rotation maximale atteinte à chaque séance du Hibou, comparée à l’angle cible prescrit.")
        target_text = f"objectif {fmt_number(target)}°" if pd.notna(target) else "objectif n.c."
        kpi_row([
            kpi_card("Rotation gauche", fmt_number(left), "←", "tone-violet", unit="°", foot=target_text,
                     delta_html=delta_chip(analytics.delta(left, first_rot["rotation_left"]), "°", 0)),
            kpi_card("Rotation droite", fmt_number(right), "→", "tone-blue", unit="°", foot=target_text,
                     delta_html=delta_chip(analytics.delta(right, first_rot["rotation_right"]), "°", 0)),
            kpi_card("Symétrie", fmt_number(sym), "⇄", "tone-green", unit=" %",
                     foot="symétrique" if sym >= 80 else "asymétrie à surveiller"),
            kpi_card("Maintien moyen", fmt_number(last_rot["hold_seconds_avg"], 1), "⏱", "tone-orange", unit=" s",
                     foot=f"fluidité {fmt_number(last_rot['smoothness'])}/100"
                     if pd.notna(last_rot["smoothness"]) else "dernière séance"),
        ])
        st.write("")
        left_col, right_col = st.columns([1.5, 1], gap="medium")
        with left_col:
            with card("amplitude"):
                card_title("Évolution de l’amplitude", "Degrés atteints à gauche et à droite, et angle cible.")
                st.plotly_chart(charts.amplitude_chart(history), config=charts.CHART_CONFIG, key="patient_amplitude")
        with right_col:
            with card("pain"):
                card_title("Douleur & effort", "Auto-évaluation de l’enfant après chaque séance (0 à 5).")
                if history[["pain_level", "effort"]].notna().any().any():
                    st.plotly_chart(charts.pain_effort_chart(history), config=charts.CHART_CONFIG, key="patient_pain")
                else:
                    st.info("Pas encore d’auto-évaluation.")

    # --------------------------------------------------------
    # ABDUCTION DE L'ÉPAULE (Le Gardien des Lucioles)
    # --------------------------------------------------------
    abduction = history.dropna(subset=["abduction_max"])
    if not abduction.empty:
        last_abd, first_abd = abduction.iloc[-1], abduction.iloc[0]
        threshold = last_abd["target_angle"]
        arm = {"R": "bras droit", "L": "bras gauche", "BI": "des deux bras", "both": "des deux bras"}.get(
            last_abd["affected_arm"], "bras entraîné")
        recent_comp = abduction.tail(3)["compensations"].mean()
        section("Élévation du bras (épaule)",
                f"Élévation du {arm} à chaque séance du Gardien des Lucioles, comparée à la hauteur prescrite.")
        kpi_row([
            kpi_card("Abduction max", fmt_number(last_abd["abduction_max"]), "↑", "tone-violet", unit="°",
                     foot=f"seuil {fmt_number(threshold)}°" if pd.notna(threshold) else "dernière séance",
                     delta_html=delta_chip(analytics.delta(last_abd["abduction_max"], first_abd["abduction_max"]), "°", 0)),
            kpi_card("Pic moyen", fmt_number(last_abd["abduction_mean_peak"]), "◠", "tone-blue", unit="°",
                     foot="moyenne des répétitions validées",
                     delta_html=delta_chip(analytics.delta(last_abd["abduction_mean_peak"],
                                                           first_abd["abduction_mean_peak"]), "°", 0)),
            kpi_card("Compensations", fmt_number(recent_comp, 1), "⚠", "tone-orange",
                     foot="moyenne des 3 dernières séances"
                     if pd.notna(recent_comp) else "non mesuré"),
            kpi_card("Lucioles", fmt_number(last_abd["repetitions"]), "✨", "tone-green",
                     foot="ramenées à la dernière séance"),
        ])
        st.write("")
        abd_col, comp_col = st.columns([1.5, 1], gap="medium")
        with abd_col:
            with card("abduction"):
                card_title("Évolution de l’abduction", "Amplitude maximale et pic moyen, avec le seuil prescrit.")
                st.plotly_chart(charts.abduction_chart(abduction), config=charts.CHART_CONFIG,
                                key="patient_abduction")
        with comp_col:
            with card("compensations"):
                card_title("Compensations", "Fois où l’autre bras s’est levé pendant la séance.")
                st.plotly_chart(charts.compensation_chart(abduction), config=charts.CHART_CONFIG,
                                key="patient_compensations")
        if rotation.empty and history[["pain_level", "effort"]].notna().any().any():
            with card("pain-lucioles"):
                card_title("Douleur & effort", "Auto-évaluation de l’enfant après chaque séance (0 à 5).")
                st.plotly_chart(charts.pain_effort_chart(history), config=charts.CHART_CONFIG,
                                key="patient_pain_lucioles")

    # --------------------------------------------------------
    # MÉMOIRE ET COORDINATION (La Danse des Lucioles, ergothérapie)
    # --------------------------------------------------------
    sequence = history.dropna(subset=["max_sequence"])
    if not sequence.empty:
        last_seq, first_seq = sequence.iloc[-1], sequence.iloc[0]
        recent = sequence.tail(3)
        section("Mémoire et coordination",
                "Séquences de fleurs reproduites avec les mains à chaque séance de La Danse des Lucioles.")
        kpi_row([
            kpi_card("Plus longue séquence", fmt_number(last_seq["max_sequence"]), "✿", "tone-violet",
                     unit=" fleurs", foot=f"record {fmt_number(sequence['max_sequence'].max())} fleurs",
                     delta_html=delta_chip(analytics.delta(last_seq["max_sequence"], first_seq["max_sequence"]), "", 0)),
            kpi_card("Erreurs d’ordre", fmt_number(recent["sequence_errors"].mean(), 1), "✗", "tone-orange",
                     foot="moyenne des 3 dernières séances"),
            kpi_card("Aides de Léo", fmt_number(recent["hints_used"].mean(), 1), "?", "tone-blue",
                     foot="moyenne des 3 dernières séances"),
            kpi_card("Temps par fleur", fmt_number(last_seq["mean_step_sec"], 1), "⏱", "tone-green", unit=" s",
                     foot="vitesse de planification du geste"),
        ])
        st.write("")
        seq_col, err_col = st.columns([1.5, 1], gap="medium")
        with seq_col:
            with card("sequence"):
                card_title("Longueur des séquences", "Plus longue danse réussie à chaque séance (mémoire de travail).")
                st.plotly_chart(charts.sequence_chart(sequence), config=charts.CHART_CONFIG, key="patient_sequence")
        with err_col:
            with card("seq-errors"):
                card_title("Erreurs et aides", "Fleurs touchées dans le mauvais ordre et aides données par Léo.")
                st.plotly_chart(charts.errors_hints_chart(sequence), config=charts.CHART_CONFIG,
                                key="patient_seq_errors")
        if rotation.empty and abduction.empty and history[["pain_level", "effort"]].notna().any().any():
            with card("pain-danse"):
                card_title("Douleur & effort", "Auto-évaluation de l’enfant après chaque séance (0 à 5).")
                st.plotly_chart(charts.pain_effort_chart(history), config=charts.CHART_CONFIG,
                                key="patient_pain_danse")

    # --------------------------------------------------------
    # ATTENTION ET CONTRÔLE DES GESTES (Le Gardien du Château, ergothérapie)
    # --------------------------------------------------------
    castle = history.dropna(subset=["nogo_success_rate"])
    if not castle.empty:
        last_c, first_c = castle.iloc[-1], castle.iloc[0]
        section("Attention et contrôle des gestes",
                "Défis faits au bon moment et statues tenues devant l’ogre, à chaque partie du Gardien du Château.")
        fade = last_c.get("accuracy_start") - last_c.get("accuracy_end") \
            if pd.notna(last_c.get("accuracy_start")) and pd.notna(last_c.get("accuracy_end")) else None
        kpi_row([
            kpi_card("Défis réussis", fmt_number(last_c["go_success_rate"]), "✦", "tone-blue", unit=" %",
                     foot="attention : bon geste au bon moment",
                     delta_html=delta_chip(analytics.delta(last_c["go_success_rate"], first_c["go_success_rate"]), "", 0)),
            kpi_card("Statues réussies", fmt_number(last_c["nogo_success_rate"]), "♜", "tone-violet", unit=" %",
                     foot="contrôle de l’impulsivité devant l’ogre",
                     delta_html=delta_chip(analytics.delta(last_c["nogo_success_rate"], first_c["nogo_success_rate"]), "", 0)),
            kpi_card("Temps de réaction", fmt_number(last_c["rt_mean_ms"]), "⏱", "tone-green", unit=" ms",
                     foot=f"variabilité ± {fmt_number(last_c['rt_sd_ms'])} ms"),
            kpi_card("Fin de partie", fmt_number(last_c["accuracy_end"]), "◔", "tone-orange", unit=" %",
                     foot=(f"{fmt_number(fade)} points de moins qu’au début" if fade is not None and fade > 0
                           else "réussite tenue jusqu’au bout")),
        ])
        st.write("")
        att_col, castle_err_col = st.columns([1.5, 1], gap="medium")
        with att_col:
            with card("attention"):
                card_title("Attention et inhibition", "Défis réussis et statues tenues devant l’ogre, par séance.")
                st.plotly_chart(charts.attention_chart(castle), config=charts.CHART_CONFIG, key="patient_attention")
        with castle_err_col:
            with card("castle-errors"):
                card_title("Types d’erreurs", "Bouger devant l’ogre (impulsivité), oublier un défi, se tromper de geste.")
                st.plotly_chart(charts.castle_errors_chart(castle), config=charts.CHART_CONFIG,
                                key="patient_castle_errors")

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
    extra = {
        "Rot. gauche (°)": "rotation_left",
        "Rot. droite (°)": "rotation_right",
        "Abduction max (°)": "abduction_max",
        "Compensations": "compensations",
        "Séquence max": "max_sequence",
        "Erreurs d’ordre": "sequence_errors",
        "Statues (%)": "nogo_success_rate",
        "Réaction (ms)": "rt_mean_ms",
        "Douleur (/5)": "pain_level",
        "Effort (/5)": "effort",
    }
    for label, column in extra.items():
        if table[column].notna().any():
            display[label] = table[column].to_numpy()
    if display["Exercice"].nunique(dropna=True) <= 1:
        display = display.drop(columns="Exercice")
    if display["Progression"].isna().all() or {"Rot. gauche (°)", "Abduction max (°)", "Séquence max", "Statues (%)"} & set(display.columns):
        display = display.drop(columns="Progression")
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
            "Rot. gauche (°)": st.column_config.NumberColumn(format="%d"),
            "Rot. droite (°)": st.column_config.NumberColumn(format="%d"),
            "Abduction max (°)": st.column_config.NumberColumn(format="%d"),
            "Compensations": st.column_config.NumberColumn(format="%d"),
            "Séquence max": st.column_config.NumberColumn(format="%d"),
            "Erreurs d’ordre": st.column_config.NumberColumn(format="%d"),
            "Douleur (/5)": st.column_config.NumberColumn(format="%d"),
            "Effort (/5)": st.column_config.NumberColumn(format="%d"),
        },
    )
    st.download_button(
        "⤓ Exporter l’historique (CSV)",
        display.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"sensai_{patient['patient_code'] or patient['id']}_seances.csv",
        mime="text/csv",
    )
    note("la « progression » est la variation du score par rapport à la séance précédente "
         "du même exercice.", title="Définition")
