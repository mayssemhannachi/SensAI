import json

import streamlit as st

from dashboard.components.ui import esc, render_html
from dashboard.utils import api_client, state
from dashboard.utils.api_client import ApiError
from dashboard.utils.theme import MASCOT_URI


def _redirect(url: str) -> None:
    """Redirige le navigateur vers ``url`` (page du site SensAI)."""
    st.html(f"<script>window.location.replace({json.dumps(url)});</script>",
            unsafe_allow_javascript=True)


def show_login():
    """Visiteur non connecté : il est renvoyé vers la connexion unique du site SensAI.

    Connexion directe de secours (si le site n'est pas lancé) : http://localhost:8501/?direct=1
    """
    site = api_client.site_url()
    target = st.session_state.pop(state.REDIRECT_KEY, "/login")
    if st.query_params.get("direct") != "1":
        st.session_state.pop(state.NOTICE_KEY, None)
        url = f"{site}{target}"
        _redirect(url)
        _, center, _ = st.columns([1, 1.25, 1])
        with center:
            render_html(
                f"""
                <div class="kk-login-head kk-fade" style="margin-top:14vh">
                  <img src="{MASCOT_URI}" alt="SensAI" style="width:72px;height:72px;object-fit:contain"/>
                  <div class="kk-subtitle" style="margin:10px auto 0">Redirecting to SensAI…</div>
                </div>
                """
            )
            st.link_button("Continue to SensAI", url, type="primary", width="stretch")
        return
    _, center, _ = st.columns([1, 1.25, 1])
    with center:
        render_html(
            f"""
            <div class="kk-login-head kk-fade" style="margin-top:6vh">
              <img src="{MASCOT_URI}" alt="SensAI" style="width:84px;height:84px;object-fit:contain"/>
              <div class="kk-title" style="font-size:28px;margin-top:6px">
                Sens<span class="kk-word-a">A</span><span class="kk-word-i">I</span> therapist space
              </div>
              <div class="kk-subtitle" style="margin:6px auto 0">
                Follow your patients, personalize their games and analyze their progress.
              </div>
            </div>
            """
        )

        notice = st.session_state.pop(state.NOTICE_KEY, None)
        if notice:
            st.info(notice)

        st.link_button("Sign in on SensAI", f"{site}/login", type="primary", width="stretch")
        render_html(
            f"<div style='text-align:center;font-size:12.5px;color:#64748B;margin:8px 0 18px'>"
            f"No account yet? <a href='{esc(site)}/register' target='_self' "
            f"style='color:#7C3AED;font-weight:800'>Create a therapist account</a></div>"
        )

        with st.expander("Direct sign-in to the dashboard"):
            if not api_client.health():
                st.warning(
                    f"The SensAI server is not responding ({api_client.api_base_url()}). "
                    "Check that the backend is running."
                )
            with st.form("backend_login_form"):
                email = st.text_input("Email address", placeholder="therapist@example.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign in", type="primary", width="stretch")

            if submitted:
                try:
                    with st.spinner("Signing in…"):
                        token = api_client.login(email.strip(), password)
                        try:
                            user = api_client.me(token)
                        except ApiError:
                            user = {"sub": email.strip(), "role": "therapist"}
                    if user.get("role", "therapist") != "therapist":
                        st.error("This is a patient account: the patient space is on the SensAI website.")
                    else:
                        state.set_data_source("api")
                        state.sign_in(token, user)
                        st.rerun()
                except ApiError as error:
                    st.error(str(error))
