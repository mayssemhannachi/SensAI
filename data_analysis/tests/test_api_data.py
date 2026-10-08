"""Normalisation des données du backend vers le format du dashboard."""

from unittest.mock import patch

import pandas as pd
import pytest

from dashboard.utils import data


def _payload():
    return {
        "patients": [
            {"id": 12, "first_name": "Demo", "last_name": "Child", "age": 8,
             "patient_code": "abc123", "therapist_id": 4, "created_at": "2026-09-01T10:00:00"},
            {"id": 13, "first_name": "Sans", "last_name": "Séance", "age": 6,
             "patient_code": "def456", "therapist_id": 4, "created_at": "2026-09-02T10:00:00"},
        ],
        "games": [{"id": 3, "name": "Wrist Wizard", "slug": "wrist-wizard", "description": None}],
        "patient_games": [{"patient_game_id": 45, "patient_id": 12, "game_id": 3, "game_name": "Wrist Wizard"}],
        "sessions": [
            data.api_session_to_row(
                {"id": 91, "duration_sec": 120, "created_at": "2026-10-05T12:00:00",
                 "metrics": {"score": 50, "success_rate": 0.6, "reps": 10, "level": 2,
                             "exercise_name": "Flexion", "played_at": "2026-09-20T09:00:00"}},
                12, 45, {"id": 3, "name": "Wrist Wizard"}),
            data.api_session_to_row(
                {"id": 92, "duration_sec": 90, "created_at": "2026-10-06T12:00:00",
                 "metrics": {"score": 60, "success_rate": 0.75, "exercise_name": "Flexion"}},
                12, 45, {"id": 3, "name": "Wrist Wizard"}),
        ],
    }


def test_api_session_row_mapping():
    row = _payload()["sessions"][0]
    assert row["session_id"] == 91
    assert row["duration_min"] == 2
    assert row["repetitions"] == 10
    assert row["level"] == 2
    assert row["exercise_name"] == "Flexion"
    # played_at (date réelle de jeu) est prioritaire sur created_at
    assert row["session_date"] == "2026-09-20T09:00:00"


def test_build_api_dataset_normalizes_everything():
    ds = data.build_api_dataset(_payload(), diagnoses={12: "Test"})
    assert list(ds.sessions.columns) == data.SESSION_COLUMNS
    assert len(ds.patients) == 2
    s = ds.sessions_of(12)
    # ratio 0-1 converti en pourcentage
    assert s["success_rate"].tolist() == [60.0, 75.0]
    # progression absente des métriques : dérivée du score (+20 %)
    assert pd.isna(s["progression"].iloc[0])
    assert s["progression"].iloc[1] == pytest.approx(20.0)
    assert s["patient_name"].iloc[0] == "Demo Child"
    assert ds.patient(12)["diagnosis"] == "Test"
    assert ds.patient(13)["diagnosis"] == ""
    assert ds.sessions_of(13).empty
    assert not ds.diagnosis_readable


def test_empty_backend_still_has_all_columns():
    ds = data.build_api_dataset({"patients": [], "games": [], "sessions": [], "patient_games": []})
    assert ds.sessions.empty and ds.patients.empty
    assert set(data.SESSION_COLUMNS) <= set(ds.sessions.columns)
    assert set(data.PATIENT_COLUMNS) <= set(ds.patients.columns)


def test_fetch_api_payload_walks_patients_games_sessions():
    calls = []

    def fake_get(path, token):
        calls.append(path)
        assert token == "tok"
        return {
            "/patients/": [{"id": 12, "first_name": "A", "last_name": "B", "age": 8}],
            "/games/": [{"id": 3, "name": "Wrist Wizard"}],
            "/patient-games/patient/12": [{"id": 45, "patient_id": 12, "game_id": 3, "configuration": {}}],
            "/sessions/patient-game/45": [
                {"id": 91, "patient_game_id": 45, "duration_sec": 60, "created_at": "2026-10-05T12:00:00",
                 "metrics": {"score": 80, "success_rate": 70}}],
            "/consultations/patient/12": [{"id": 1, "diagnosis": "Torticolis"}],
        }[path]

    with patch.object(data, "api_get", side_effect=fake_get):
        payload = data.fetch_api_payload("tok")
    assert len(payload["sessions"]) == 1
    assert payload["sessions"][0]["game_name"] == "Wrist Wizard"
    assert payload["patient_games"][0]["patient_game_id"] == 45
    assert "/sessions/patient-game/45" in calls
    assert payload["diagnoses"] == {12: "Torticolis"} and payload["diagnosis_readable"]


def test_demo_dataset_is_consistent():
    ds = data.load_demo_dataset()
    assert ds.is_demo
    assert not ds.patients.empty and not ds.sessions.empty
    assert ds.patients["age"].notna().all()
    assert set(ds.sessions["patient_id"]) <= set(ds.patients["id"])
    assert ds.sessions["success_rate"].between(0, 100).all()
    assert ds.sessions["session_date"].notna().all()


def test_age_from_birth_date():
    ages = data.age_from_birth_date(pd.Series(["2018-10-09", "2018-10-08"]), pd.Timestamp("2026-10-08"))
    assert ages.tolist() == [7, 8]
