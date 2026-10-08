"""Rendu de chaque page en mode démo, sans exception (Streamlit AppTest)."""

import pytest
from streamlit.testing.v1 import AppTest

from dashboard.utils import data


def _script(module, function):
    import importlib
    import sys
    from pathlib import Path

    root = Path.cwd()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from dashboard.utils.theme import apply_theme

    apply_theme()
    getattr(importlib.import_module(module), function)()


def _app(module, function):
    return AppTest.from_function(_script, args=(module, function), default_timeout=30)


PAGES = [
    ("dashboard.pages.global_view", "show_global_view"),
    ("dashboard.pages.patients", "show_patients"),
    ("dashboard.pages.patient_detail", "show_patient_detail"),
    ("dashboard.pages.games", "show_games"),
    ("dashboard.pages.add_patient", "show_add_patient"),
]


@pytest.mark.parametrize("module,function", PAGES)
def test_page_renders_in_demo_mode(module, function):
    at = _app(module, function)
    at.session_state["data_source"] = "demo"
    at.run()
    assert not at.exception, at.exception


def test_every_patient_sheet_renders():
    ids = data.load_demo_dataset().patients["id"].tolist()
    for patient_id in ids:
        at = _app("dashboard.pages.patient_detail", "show_patient_detail")
        at.session_state["data_source"] = "demo"
        at.session_state["selected_patient_id"] = patient_id
        at.run()
        assert not at.exception, (patient_id, at.exception)


@pytest.mark.parametrize("period", ["7 jours", "30 jours", "90 jours", "Tout"])
def test_overview_all_periods(period):
    at = _app("dashboard.pages.global_view", "show_global_view")
    at.session_state["data_source"] = "demo"
    at.session_state["overview_period"] = period
    at.run()
    assert not at.exception, at.exception


def test_demo_add_patient_flow():
    at = _app("dashboard.pages.add_patient", "show_add_patient")
    at.session_state["data_source"] = "demo"
    at.run()
    at.text_input[0].input("Lina")
    at.text_input[1].input("Test")
    at.button[0].click()
    at.run()
    assert not at.exception
    created, warning = at.session_state["last_created_patient"]
    assert created["first_name"] == "Lina" and warning is None


def test_full_app_demo_mode():
    at = AppTest.from_file("../dashboard/app.py", default_timeout=30)
    at.session_state["data_source"] = "demo"
    at.run()
    assert not at.exception, at.exception


def test_full_app_backend_mode_shows_login(monkeypatch):
    monkeypatch.setenv("KINEKIDS_API_URL", "http://127.0.0.1:9")  # backend volontairement absent
    at = AppTest.from_file("../dashboard/app.py", default_timeout=30)
    at.session_state["data_source"] = "api"
    at.run()
    assert not at.exception, at.exception
    assert any("Se connecter" in b.label for b in at.button) or at.get("form_submit_button")
