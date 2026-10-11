import streamlit as st

from dashboard import navigation
from dashboard.components import game_settings
from dashboard.components.ui import badge, esc, note, page_header, render_html
from dashboard.utils import api_client, state
from dashboard.utils.api_client import ApiError, ApiPartialSuccessError
from dashboard.utils.data import (
    assign_game,
    create_activation_code,
    load_dataset,
    playable_games,
    save_patient,
)

CREATED_KEY = "last_created_patient"


def _created_banner() -> None:
    created = st.session_state.get(CREATED_KEY) or {}
    patient = created.get("patient") or {}
    name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
    code = created.get("code")
    game = created.get("game")
    config = created.get("config") or {}
    site = api_client.site_url()

    game_line = ""
    if game:
        if "affected_arm" in config:
            arm = {"R": "right arm", "L": "left arm", "BI": "both arms"}.get(config.get("affected_arm"), "arm")
            details = (f"{arm} · "
                       f"threshold {config.get('target_angle')}° · elbow ≥ {config.get('elbow_min')}° · "
                       f"{config.get('repetitions')} fireflies")
        else:
            details = (f"angle {config.get('target_angle')}° · hold {config.get('hold_seconds')} s · "
                       f"{config.get('repetitions')} repetitions · limit {config.get('safety_limit')}°")
        game_line = (
            f"<div class='kk-card-sub' style='margin-top:6px'>Prescribed game: <b>{esc(game)}</b> · "
            f"{esc(details)}</div>"
        )
    code_block = ""
    if code:
        code_block = f"""
        <div style="margin-top:16px;padding:16px;border-radius:20px;background:#F5F3FF;border:1px dashed #C4B5FD;text-align:center">
          <div class="kk-kicker">Activation code to give to the patient</div>
          <div data-testid="activation-code" style="font:900 34px 'Outfit',sans-serif;letter-spacing:.35em;color:#7C3AED;margin:6px 0">{esc(code)}</div>
          <div class="kk-card-sub">The patient (or their parent) goes to <b>{esc(site)}/activate</b>, enters this code, then
          creates an email and password. The code is valid for 30 days and can be used only once.</div>
        </div>"""
    render_html(
        f"""
        <div class="kk-kpi kk-fade" style="min-height:0;margin-bottom:14px">
          <div class="kk-kpi-top">
            <div class="kk-kpi-icon tone-green">✓</div>
            <div>
              <div class="kk-card-title">Patient created: {esc(name)}</div>
              <div class="kk-card-sub">Patient code {esc(str(patient.get('patient_code', '')).upper())}</div>
            </div>
          </div>
          {game_line}
          {code_block}
        </div>
        """
    )
    for warning in created.get("warnings", []):
        st.warning(warning)

    col_open, col_new, _ = st.columns([1, 1, 2])
    with col_open:
        if st.button("Open record →", type="primary", width="stretch"):
            st.session_state.pop(CREATED_KEY, None)
            navigation.open_patient(int(patient["id"]))
    with col_new:
        if st.button("Create another patient", width="stretch"):
            st.session_state.pop(CREATED_KEY, None)
            for key in [k for k in st.session_state if str(k).startswith(("np_", "new_"))]:
                st.session_state.pop(key, None)
            st.rerun()


def show_add_patient():
    backend = state.api_mode_enabled()
    page_header(
        "New care pathway",
        "New patient",
        "Create the child's profile, prescribe their game with your settings, then give them their activation code.",
    )

    if st.session_state.get(CREATED_KEY):
        _created_banner()
        return

    games = playable_games(load_dataset().games) if backend else None

    center, side = st.columns([1, 0.42], gap="large")
    with center:
        with st.container(border=True):
            render_html('<div class="kk-card-title">1 · Identity</div>')
            col1, col2, col3 = st.columns([1.2, 1.2, 0.7])
            with col1:
                first_name = st.text_input("First name *", placeholder="e.g. Salma", max_chars=100, key="np_first")
            with col2:
                last_name = st.text_input("Last name *", placeholder="e.g. Ben Ali", max_chars=100, key="np_last")
            with col3:
                age = st.number_input("Age *", min_value=1, max_value=18, value=8, step=1, key="np_age")

            render_html('<div class="kk-card-title" style="margin-top:10px">2 · Clinical information</div>')
            diagnosis = st.text_area(
                "Diagnosis",
                placeholder="e.g. post-traumatic torticollis, hemiplegia, shoulder stiffness…",
                height=80,
                key="np_dx",
            )

            game_id = None
            config = None
            slug = None
            if backend:
                render_html('<div class="kk-card-title" style="margin-top:10px">3 · Prescribed game and settings</div>')
                if games is None or games.empty:
                    if state.current_user().get("specialty") == "ergotherapist":
                        st.caption(
                            "The occupational therapy catalog is intended for cognitive and "
                            "coordination games. These games are not playable yet; you can "
                            "create the patient record and generate their activation code."
                        )
                    else:
                        st.caption("No games available at the moment.")
                else:
                    by_id = games.set_index("id")
                    game_id = st.segmented_control(
                        "Game", games["id"].tolist(), default=games["id"].iloc[0],
                        format_func=lambda gid: by_id.loc[gid, "name"], key="new_patient_game",
                    )
                    if game_id is not None:
                        slug = by_id.loc[game_id, "slug"]
                        st.caption(game_settings.GAME_HINTS.get(slug, ""))
                        config = {**game_settings.settings_fields(slug, None, f"new_{slug}"), "active": True}

            submitted = st.button(
                "Create patient and generate code" if backend else "Create profile",
                type="primary", width="stretch",
            )

    with side:
        render_html(
            f"""
            <div class="kk-kpi" style="min-height:0">
              <div class="kk-card-title">How does it work?</div>
              <div class="kk-card-sub" style="line-height:1.7;margin-top:8px">
                {badge('1', 'brand')} You create the patient and prescribe their game.<br/>
                {badge('2', 'brand')} A 6-character activation code is generated.<br/>
                {badge('3', 'brand')} The patient activates their account on the SensAI website.<br/>
                {badge('4', 'brand')} They play at home: each session arrives here automatically.
              </div>
            </div>
            """
        )
        if not backend:
            note("offline mode: the patient is added in memory, without a game or code.", title="Demo")

    if not submitted:
        return

    errors = []
    if not first_name.strip():
        errors.append("First name is required.")
    if not last_name.strip():
        errors.append("Last name is required.")
    if config is not None and (problem := game_settings.validate(slug, config)):
        errors.append(problem)
    if errors:
        for error in errors:
            st.error(error)
        return

    warnings = []
    try:
        with st.spinner("Creating patient…"):
            try:
                patient = save_patient(first_name, last_name, age=int(age), diagnosis=diagnosis)
            except ApiPartialSuccessError as error:
                patient = error.patient
                warnings.append(str(error))

            result = {"patient": patient, "warnings": warnings}
            if backend and game_id is not None:
                try:
                    assign_game(patient["id"], int(game_id), config)
                    result["game"] = games.set_index("id").loc[game_id, "name"]
                    result["config"] = config
                except ApiError as error:
                    if error.status_code == 401:
                        raise
                    warnings.append(f"The game could not be assigned: {error}")
            if backend:
                try:
                    result["code"] = create_activation_code(patient["id"])["code"]
                except ApiError as error:
                    if error.status_code == 401:
                        raise
                    warnings.append(f"The activation code could not be generated: {error}")
        st.session_state[CREATED_KEY] = result
        st.rerun()
    except ApiError as error:
        if error.status_code == 401:
            raise
        st.error(f"The server rejected the creation: {error}")
    except ValueError as error:
        st.error(str(error))
