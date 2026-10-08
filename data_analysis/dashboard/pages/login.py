import streamlit as st

from dashboard.components.ui import esc, render_html
from dashboard.utils import api_client, state
from dashboard.utils.api_client import ApiError


def show_login():
    _, center, _ = st.columns([1, 1.3, 1])
    with center:
        render_html(
            """
            <div class="kk-login-head kk-fade" style="margin-top:6vh">
              <div class="kk-brand-logo">K</div>
              <div class="kk-title" style="font-size:26px">Connexion thérapeute</div>
              <div class="kk-subtitle" style="margin:6px auto 0">
                Connectez-vous avec votre compte KineKids AI pour accéder
                aux données réelles de vos patients.
              </div>
            </div>
            """
        )

        notice = st.session_state.pop(state.NOTICE_KEY, None)
        if notice:
            st.info(notice)

        if not api_client.health():
            st.warning(
                f"Le backend ne répond pas à l’adresse {api_client.api_base_url()}. "
                "Démarrez l’API (uvicorn app.main:app) ou utilisez le mode démo."
            )

        with st.form("backend_login_form"):
            email = st.text_input("Adresse e-mail", placeholder="therapeute@exemple.com")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", type="primary", width="stretch")

        if submitted:
            try:
                with st.spinner("Connexion…"):
                    token = api_client.login(email.strip(), password)
                    try:
                        user = api_client.me(token)
                    except ApiError:
                        user = {"sub": email.strip()}
                state.sign_in(token, user)
                st.rerun()
            except ApiError as error:
                st.error(str(error))

        st.write("")
        if st.button("Continuer avec les données de démo", width="stretch"):
            state.set_data_source("demo")
            st.rerun()

        render_html(
            f'<div class="kk-side-foot">API : {esc(api_client.api_base_url())}</div>'
        )
