"""Contrat d'écriture vers le backend (création patient, diagnostic, jeux)."""

from unittest.mock import patch

import pytest

from dashboard.utils import data
from dashboard.utils.api_client import ApiError, ApiPartialSuccessError

CREATED = {"id": 31, "first_name": "Demo", "last_name": "Child", "age": 8,
           "patient_code": "server-code", "therapist_id": 2, "created_at": "2026-10-05T12:00:00"}


def _api_mode():
    return (
        patch.object(data.state, "api_mode_enabled", return_value=True),
        patch.object(data.state, "get_token", return_value="tok"),
        patch.object(data, "refresh_data"),
        patch.object(data, "_session_diagnoses", return_value={}),
    )


def test_create_patient_sends_backend_fields_then_consultation():
    a, b, c, d = _api_mode()
    with a, b, c, d, patch.object(data, "api_post", side_effect=[CREATED, {"id": 76}]) as post:
        result = data.save_patient(" Demo ", " Child ", age=8, diagnosis="Coordination")
    assert result == CREATED
    assert post.call_args_list[0].args == (
        "/patients/", "tok", {"first_name": "Demo", "last_name": "Child", "age": 8})
    path, _, body = post.call_args_list[1].args
    assert path == "/consultations/"
    assert body["patient_id"] == 31 and body["diagnosis"] == "Coordination"


def test_diagnosis_failure_is_partial_success():
    a, b, c, d = _api_mode()
    with a, b, c, d, patch.object(data, "api_post", side_effect=[CREATED, ApiError("boom", 500)]):
        with pytest.raises(ApiPartialSuccessError) as info:
            data.save_patient("Demo", "Child", age=8, diagnosis="X")
    assert info.value.patient["id"] == 31


def test_patient_requires_names_and_age():
    with pytest.raises(ValueError):
        data.save_patient("", "Child", age=8)
    with pytest.raises(ValueError):
        data.save_patient("Demo", "Child", age=None)


def test_assign_game_payload():
    a, b, c, d = _api_mode()
    with a, b, c, d, patch.object(data, "api_post", return_value={"id": 5}) as post:
        data.assign_game(31, 3)
    assert post.call_args.args == (
        "/patient-games/", "tok", {"patient_id": 31, "game_id": 3, "configuration": {}})


def test_assign_game_refused_in_demo():
    with patch.object(data.state, "api_mode_enabled", return_value=False):
        with pytest.raises(ValueError):
            data.assign_game(1, 1)
