import streamlit as st

from dashboard.components.ui import esc, render_html
from dashboard.utils import api_client, state
from dashboard.utils.api_client import ApiError
from dashboard.utils.theme import MASCOT_URI


def show_login():
    """Page affichée sans session : on renvoie vers la connexion du site SensAI.

    Une connexion directe reste possible (utile si le site n'est pas lancé).
    """
    site = api_client.site_url()
    _, center, _ = st.columns([1, 1.25, 1])
    with center:
        render_html(
            f"""
            <div class="kk-login-head kk-fade" style="margin-top:6vh">
              <img src="{MASCOT_URI}" alt="SensAI" style="width:84px;height:84px;object-fit:contain"/>
              <div class="kk-title" style="font-size:28px;margin-top:6px">
                Espace thérapeute Sens<span class="kk-word-a">A</span><span class="kk-word-i">I</span>
              </div>
              <div class="kk-subtitle" style="margin:6px auto 0">
                Suivez vos patients, personnalisez leurs jeux et analysez leur progression.
              </div>
            </div>
            """
        )

        notice = st.session_state.pop(state.NOTICE_KEY, None)
        if notice:
            st.info(notice)

        st.link_button("Se connecter sur SensAI", f"{site}/login", type="primary", width="stretch")
        render_html(
            f"<div style='text-align:center;font-size:12.5px;color:#64748B;margin:8px 0 18px'>"
            f"Pas encore de compte ? <a href='{esc(site)}/register' target='_self' "
            f"style='color:#7C3AED;font-weight:800'>Créer un compte thérapeute</a></div>"
        )

        with st.expander("Connexion directe au dashboard"):
            if not api_client.health():
                st.warning(
                    f"Le serveur SensAI ne répond pas ({api_client.api_base_url()}). "
                    "Vérifiez que le backend est démarré."
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
                            user = {"sub": email.strip(), "role": "therapist"}
                    if user.get("role", "therapist") != "therapist":
                        st.error("Ce compte est un compte patient : son espace se trouve sur le site SensAI.")
                    else:
                        state.set_data_source("api")
                        state.sign_in(token, user)
                        st.rerun()
                except ApiError as error:
                    st.error(str(error))
