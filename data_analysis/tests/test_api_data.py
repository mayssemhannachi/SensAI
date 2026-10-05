import unittest
from unittest.mock import patch

import pandas as pd

from dashboard.utils import data


class ApiSessionNormalizationTests(unittest.TestCase):
    def test_backend_session_is_normalized_for_dashboard(self):
        patients = pd.DataFrame(
            [
                {
                    "id": 12,
                    "first_name": "Demo",
                    "last_name": "Child",
                    "age": 8,
                    "patient_code": "demo-code",
                    "therapist_id": 4,
                }
            ]
        )
        games = pd.DataFrame([{"id": 3, "name": "Wrist Wizard"}])

        def fake_get(path, token):
            self.assertEqual(token, "test-token")
            if path == "/patient-games/patient/12":
                return [{"id": 45, "patient_id": 12, "game_id": 3, "configuration": {}}]
            if path == "/sessions/patient-game/45":
                return [
                    {
                        "id": 91,
                        "patient_game_id": 45,
                        "duration_sec": 120,
                        "metrics": {
                            "score": 82,
                            "success_rate": 75,
                            "progression": 5,
                            "reps": 10,
                            "level": 2,
                            "exercise_id": 7,
                            "exercise_name": "Wrist movement",
                        },
                        "created_at": "2026-10-05T12:00:00",
                    }
                ]
            self.fail(f"Unexpected API path: {path}")

        with (
            patch.object(data, "_api_token", return_value="test-token"),
            patch.object(data, "load_patients", return_value=patients),
            patch.object(data, "load_games", return_value=games),
            patch.object(data, "api_get", side_effect=fake_get),
        ):
            result = data._load_api_session_analysis()

        self.assertEqual(len(result), 1)
        row = result.iloc[0]
        self.assertEqual(row["id_session"], 91)
        self.assertEqual(row["patient_id"], 12)
        self.assertEqual(row["name_game"], "Wrist Wizard")
        self.assertEqual(row["duration"], 2)
        self.assertEqual(row["success_rate"], 75)
        self.assertEqual(row["repetitions"], 10)
        self.assertEqual(row["level_number"], 2)
        self.assertEqual(row["name"], "Wrist movement")
        self.assertEqual(row["session_date"], pd.Timestamp("2026-10-05T12:00:00"))

    def test_empty_backend_history_still_has_dashboard_columns(self):
        patients = pd.DataFrame(
            [{"id": 12, "first_name": "Demo", "last_name": "Child"}]
        )
        games = pd.DataFrame(columns=["id", "name"])
        with (
            patch.object(data, "_api_token", return_value="test-token"),
            patch.object(data, "load_patients", return_value=patients),
            patch.object(data, "load_games", return_value=games),
            patch.object(data, "api_get", return_value=[]),
        ):
            result = data._load_api_session_analysis()

        self.assertTrue(result.empty)
        self.assertIn("session_date", result.columns)
        self.assertIn("success_rate", result.columns)


if __name__ == "__main__":
    unittest.main()
