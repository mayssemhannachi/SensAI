import unittest
from unittest.mock import patch

from dashboard.utils import data


class PatientApiContractTests(unittest.TestCase):
    def test_create_patient_sends_backend_fields_and_saves_diagnosis_separately(self):
        created_patient = {
            "id": 31,
            "first_name": "Demo",
            "last_name": "Child",
            "age": 8,
            "patient_code": "server-code",
            "therapist_id": 2,
            "created_at": "2026-10-05T12:00:00",
        }

        with (
            patch.object(data, "api_mode_enabled", return_value=True),
            patch.object(data, "_api_token", return_value="test-token"),
            patch.object(data, "api_post", side_effect=[created_patient, {"id": 76}]) as post,
        ):
            result = data.save_patient(
                first_name=" Demo ",
                last_name=" Child ",
                age=8,
                diagnosis="Test diagnosis",
                date_of_birth=None,
                patient_code=None,
            )

        self.assertEqual(result, created_patient)
        self.assertEqual(
            post.call_args_list[0].args,
            (
                "/patients/",
                "test-token",
                {"first_name": "Demo", "last_name": "Child", "age": 8},
            ),
        )
        self.assertEqual(post.call_args_list[1].args[0], "/consultations/")
        self.assertEqual(
            post.call_args_list[1].args[2]["patient_id"],
            created_patient["id"],
        )
        self.assertEqual(
            post.call_args_list[1].args[2]["diagnosis"],
            "Test diagnosis",
        )

    def test_api_mode_requires_age_not_demo_fields(self):
        with (
            patch.object(data, "api_mode_enabled", return_value=True),
            patch.object(data, "_api_token", return_value="test-token"),
        ):
            with self.assertRaisesRegex(ValueError, "attend l’âge"):
                data.save_patient(
                    first_name="Demo",
                    last_name="Child",
                    date_of_birth="2018-01-01",
                    patient_code="manual-code",
                )


if __name__ == "__main__":
    unittest.main()
