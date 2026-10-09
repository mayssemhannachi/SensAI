import streamlit as st

from dashboard import navigation
from dashboard.components.ui import badge, esc, note, page_header, render_html
from dashboard.utils import api_client, state
from dashboard.utils.api_client import ApiError, ApiPartialSuccessError
from dashboard.utils.data import (
    GAME_SETTINGS_DEFAULTS,
    assign_game,
    create_activation_code,
    load_dataset,
    playable_games,
    save_patient,
)

CREATED_KEY = "last_created_patient"
SPEEDS = {"lente": "Lente", "moderee": "Modérée", "rapide": "Rapide"}
DIFFICULTIES = {"faible": "Faible", "moyenne": "Moyenne", "elevee": "Élevée"}


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
        game_line = (
            f"<div class='kk-card-sub' style='margin-top:6px'>Jeu prescrit : <b>{esc(game)}</b> · "
            f"angle {config.get('target_angle')}° · maintien {config.get('hold_seconds')} s · "
            f"{config.get('repetitions')} répétitions · limite {config.get('safety_limit')}°</div>"
        )
    code_block = ""
    if code:
        code_block = f"""
        <div style="margin-top:16px;padding:16px;border-radius:20px;background:#F5F3FF;border:1px dashed #C4B5FD;text-align:center">
          <div class="kk-kicker">Code d’activation à remettre au patient</div>
          <div data-testid="activation-code" style="font:900 34px 'Outfit',sans-serif;letter-spacing:.35em;color:#7C3AED;margin:6px 0">{esc(code)}</div>
          <div class="kk-card-sub">Le patient (ou son parent) va sur <b>{esc(site)}/activate</b>, saisit ce code puis
          crée son e-mail et son mot de passe. Code valable 30 jours, utilisable une seule fois.</div>
        </div>"""
    render_html(
        f"""
        <div class="kk-kpi kk-fade" style="min-height:0;margin-bottom:14px">
          <div class="kk-kpi-top">
            <div class="kk-kpi-icon tone-green">✓</div>
            <div>
              <div class="kk-card-title">Patient créé : {esc(name)}</div>
              <div class="kk-card-sub">Code patient {esc(str(patient.get('patient_code', '')).upper())}</div>
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
        if st.button("Ouvrir la fiche →", type="primary", width="stretch"):
            st.session_state.pop(CREATED_KEY, None)
            navigation.open_patient(int(patient["id"]))
    with col_new:
        if st.button("Créer un autre patient", width="stretch"):
            st.session_state.pop(CREATED_KEY, None)
            st.rerun()


def show_add_patient():
    backend = state.api_mode_enabled()
    page_header(
        "Nouveau parcours",
        "Nouveau patient",
        "Créez le profil de l’enfant, prescrivez son jeu avec vos réglages, puis remettez-lui son code d’activation.",
    )

    if st.session_state.get(CREATED_KEY):
        _created_banner()
        return

    games = playable_games(load_dataset().games) if backend else None

    center, side = st.columns([1, 0.42], gap="large")
    with center:
        with st.form("add_patient_form", clear_on_submit=False):
            render_html('<div class="kk-card-title">1 · Identité</div>')
            col1, col2, col3 = st.columns([1.2, 1.2, 0.7])
            with col1:
                first_name = st.text_input("Prénom *", placeholder="Ex. : Salma", max_chars=100)
            with col2:
                last_name = st.text_input("Nom *", placeholder="Ex. : Ben Ali", max_chars=100)
            with col3:
                age = st.number_input("Âge *", min_value=1, max_value=18, value=8, step=1)

            render_html('<div class="kk-card-title" style="margin-top:10px">2 · Informations cliniques</div>')
            diagnosis = st.text_area(
                "Diagnostic",
                placeholder="Ex. : torticolis post-traumatique, raideur cervicale…",
                height=80,
            )

            game_id = None
            config = None
            if backend:
                render_html('<div class="kk-card-title" style="margin-top:10px">3 · Jeu prescrit et réglages</div>')
                if games is None or games.empty:
                    st.caption("Aucun jeu disponible pour le moment.")
                else:
                    game_id = st.selectbox(
                        "Jeu", games["id"].tolist(),
                        format_func=lambda gid: games.set_index("id").loc[gid, "name"],
                    )
                    d = GAME_SETTINGS_DEFAULTS
                    g1, g2, g3 = st.columns(3)
                    with g1:
                        target = st.number_input("Angle cible (°)", 5, 90, d["target_angle"], step=5,
                                                 help="Rotation du cou à atteindre de chaque côté.")
                        safety = st.number_input("Limite de sécurité (°)", 5, 120, d["safety_limit"], step=5,
                                                 help="Au-delà, le jeu demande à l’enfant de revenir doucement.")
                    with g2:
                        hold = st.number_input("Maintien (s)", 1, 15, d["hold_seconds"])
                        reps = st.number_input("Répétitions", 1, 30, d["repetitions"])
                    with g3:
                        speed = st.selectbox("Vitesse", list(SPEEDS), format_func=SPEEDS.get)
                        difficulty = st.selectbox("Difficulté", list(DIFFICULTIES), index=1,
                                                  format_func=DIFFICULTIES.get)
                    config = {**d, "target_angle": int(target), "safety_limit": int(safety),
                              "hold_seconds": int(hold), "repetitions": int(reps),
                              "speed": speed, "difficulty": difficulty, "active": True}

            submitted = st.form_submit_button(
                "Créer le patient et générer son code" if backend else "Créer le profil",
                type="primary", width="stretch",
            )

    with side:
        render_html(
            f"""
            <div class="kk-kpi" style="min-height:0">
              <div class="kk-card-title">Comment ça marche ?</div>
              <div class="kk-card-sub" style="line-height:1.7;margin-top:8px">
                {badge('1', 'brand')} Vous créez le patient et prescrivez son jeu.<br/>
                {badge('2', 'brand')} Un code d’activation à 6 caractères est généré.<br/>
                {badge('3', 'brand')} Le patient active son compte sur le site SensAI.<br/>
                {badge('4', 'brand')} Il joue chez lui : chaque séance arrive ici automatiquement.
              </div>
            </div>
            """
        )
        if not backend:
            note("mode hors-ligne : le patient est ajouté en mémoire, sans jeu ni code.", title="Démo")

    if not submitted:
        return

    errors = []
    if not first_name.strip():
        errors.append("Le prénom est obligatoire.")
    if not last_name.strip():
        errors.append("Le nom est obligatoire.")
    if errors:
        for error in errors:
            st.error(error)
        return

    warnings = []
    try:
        with st.spinner("Création du patient…"):
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
                    warnings.append(f"Le jeu n’a pas pu être attribué : {error}")
            if backend:
                try:
                    result["code"] = create_activation_code(patient["id"])["code"]
                except ApiError as error:
                    if error.status_code == 401:
                        raise
                    warnings.append(f"Le code d’activation n’a pas pu être généré : {error}")
        st.session_state[CREATED_KEY] = result
        st.rerun()
    except ApiError as error:
        if error.status_code == 401:
            raise
        st.error(f"Le serveur a refusé la création : {error}")
    except ValueError as error:
        st.error(str(error))
