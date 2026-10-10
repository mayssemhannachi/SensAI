import unittest
from datetime import date

from pydantic import ValidationError

from app.schemas.chat_schema import (
    ChatPeriod,
    ChatPeriodAnalyzed,
    ChatRequest,
    ChatResponse,
    ChatSourcesUsed,
)


class ChatSchemaTests(unittest.TestCase):
    def test_minimal_and_comparison_requests_are_valid(self):
        request = ChatRequest(patient_id=1, question=" Résume le patient ")
        self.assertEqual(request.question, "Résume le patient")
        self.assertIsNone(request.period)
        self.assertIsNone(request.comparison_period)

        comparison = ChatRequest.model_validate(
            {
                "patient_id": 3,
                "question": "Compare les périodes",
                "conversation_id": "compare-1",
                "period": {"start_date": "2026-08-01", "end_date": "2026-08-14"},
                "comparison_period": {
                    "start_date": "2026-08-15",
                    "end_date": "2026-08-31",
                },
            }
        )
        self.assertEqual(comparison.period.end_date, date(2026, 8, 14))
        self.assertEqual(comparison.comparison_period.start_date, date(2026, 8, 15))

    def test_patient_question_and_correlation_constraints(self):
        invalid_payloads = [
            {"patient_id": 0, "question": "Résumé"},
            {"patient_id": -1, "question": "Résumé"},
            {"patient_id": True, "question": "Résumé"},
            {"patient_id": 1.5, "question": "Résumé"},
            {"patient_id": "1", "question": "Résumé"},
            {"patient_id": 1, "question": "  "},
            {"patient_id": 1, "question": "x" * 4001},
            {"patient_id": 1, "question": "Résumé", "therapist_id": 7},
            {"patient_id": 1, "question": "Résumé", "role": "therapist"},
            {"patient_id": 1, "question": "Résumé", "conversation_id": " "},
            {
                "patient_id": 1,
                "question": "Compare",
                "comparison_period": {"start_date": "2026-09-01"},
            },
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                ChatRequest.model_validate(payload)

    def test_partial_period_is_allowed_and_reversed_period_is_rejected(self):
        self.assertEqual(ChatPeriod(start_date="2026-09-01").start_date, date(2026, 9, 1))
        self.assertEqual(ChatPeriod(end_date="2026-09-30").end_date, date(2026, 9, 30))
        with self.assertRaises(ValidationError):
            ChatPeriod(start_date="2026-10-01", end_date="2026-09-30")
        with self.assertRaises(ValidationError):
            ChatPeriod(start_date="2026-9-1")

    def test_response_supports_comparison_period_and_nullable_analysis(self):
        response = ChatResponse(
            patient_id=1,
            conversation_id=None,
            period_analyzed=ChatPeriodAnalyzed(
                requested_start_date=date(2026, 9, 1),
                requested_end_date=date(2026, 9, 14),
                observed_start_date=date(2026, 9, 2),
                observed_end_date=date(2026, 9, 13),
            ),
            comparison_period_analyzed=ChatPeriodAnalyzed(
                requested_start_date=date(2026, 9, 15),
                requested_end_date=date(2026, 9, 30),
                observed_start_date=None,
                observed_end_date=None,
            ),
            sources_used=ChatSourcesUsed(
                consultations=0,
                consultation_notes=0,
                sessions=0,
                sessions_with_metrics=0,
                session_events=0,
            ),
            sources=[],
            analysis=None,
            limitations=["Aucune analyse possible."],
        )
        payload = response.model_dump(mode="json")
        self.assertIsNone(payload["analysis"])
        self.assertIsNone(payload["comparison_period_analyzed"]["observed_start_date"])


if __name__ == "__main__":
    unittest.main()