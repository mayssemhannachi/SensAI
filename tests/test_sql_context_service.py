import unittest
from unittest.mock import Mock, patch
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.ai.chat_service import answer_chat
from app.ai.sql_context_service import build_sql_patient_context
from app.ai.vector_store_service import (
    index_patient_consultation_notes,
    is_vector_store_available,
)
from app.database.base import Base
from app.models.consultation import Consultation
from app.models.consultation_note import ConsultationNote
from app.models.game import Game
from app.models.patient import Patient
from app.models.patient_game import PatientGame
from app.models.session import Session as GameSession
from app.models.session_event import SessionEvent
from app.models.user import User
from app.schemas.chat_schema import (
    ChatPeriod,
    ChatPeriodAnalyzed,
    ChatRequest,
    ChatResponse,
    ChatSourcesUsed,
    ChatSourceReference,
)
class SqlContextServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)

        with self.session_factory() as db:
            previous_therapist = User(
                full_name="Previous Therapist",
                email="previous@example.com",
                password="unused",
                role="therapist",
            )
            current_therapist = User(
                full_name="Current Therapist",
                email="current@example.com",
                password="unused",
                role="therapist",
            )
            db.add_all([previous_therapist, current_therapist])
            db.flush()

            patient = Patient(
                first_name="Case",
                last_name="Patient",
                age=10,
                patient_code="PATIENT01",
                therapist_id=current_therapist.id,
            )
            game = Game(name="Coordination", slug="coordination")
            db.add_all([patient, game])
            db.flush()

            consultation = Consultation(
                patient_id=patient.id,
                therapist_id=previous_therapist.id,
                consultation_date=date(2026, 9, 10),
                diagnosis="Must never enter chatbot context",
            )
            patient_game = PatientGame(
                patient_id=patient.id,
                game_id=game.id,
                configuration={},
            )
            db.add_all([consultation, patient_game])
            db.flush()

            note = ConsultationNote(
                consultation_id=consultation.id,
                therapist_id=previous_therapist.id,
                note="Observation text",
                created_at=datetime(2026, 9, 11, 12),
            )
            session = GameSession(
                patient_game_id=patient_game.id,
                duration_sec=45,
                metrics={"score": 7},
                created_at=datetime(2026, 9, 12, 9),
            )
            db.add_all([note, session])
            db.flush()
            db.add(
                SessionEvent(
                    session_id=session.id,
                    timestamp_sec=5.0,
                    event_data={"action": "completed"},
                )
            )
            db.commit()
            self.patient_id = patient.id
            self.current_therapist_id = current_therapist.id
            self.previous_therapist_id = previous_therapist.id

    def tearDown(self):
        self.engine.dispose()

    def test_context_is_owner_scoped_and_period_limited(self):
        with self.session_factory() as db:
            context = build_sql_patient_context(
                db,
                self.patient_id,
                self.current_therapist_id,
                ChatPeriod(start_date=date(2026, 9, 1), end_date=date(2026, 9, 30)),
            )

        self.assertEqual(context.patient, {"patient_id": self.patient_id, "age": 10})
        self.assertEqual(context.sources_used.consultations, 1)
        self.assertEqual(context.sources_used.consultation_notes, 1)
        self.assertEqual(context.sources_used.sessions, 1)
        self.assertEqual(context.sources_used.sessions_with_metrics, 1)
        self.assertEqual(context.sources_used.session_events, 1)
        self.assertEqual(context.period_analyzed.observed_start_date, date(2026, 9, 10))
        self.assertEqual(context.period_analyzed.observed_end_date, date(2026, 9, 12))
        self.assertNotIn("text", context.consultation_notes[0])
        self.assertNotIn("diagnosis", context.consultations[0])
        self.assertEqual(len(context.source_references), 4)

    def test_previous_owner_is_forbidden_and_missing_patient_is_not_found(self):
        with self.session_factory() as db:
            with self.assertRaises(HTTPException) as forbidden:
                build_sql_patient_context(
                    db,
                    self.patient_id,
                    self.previous_therapist_id,
                )
            self.assertEqual(forbidden.exception.status_code, 403)

            with self.assertRaises(HTTPException) as missing:
                build_sql_patient_context(db, 99999, self.current_therapist_id)
            self.assertEqual(missing.exception.status_code, 404)

    def test_empty_period_has_no_observed_dates_and_reports_limits(self):
        requested_period = ChatPeriod(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
        with self.session_factory() as db:
            context = build_sql_patient_context(
                db,
                self.patient_id,
                self.current_therapist_id,
                requested_period,
            )

        self.assertEqual(context.period_analyzed.requested_start_date, date(2025, 1, 1))
        self.assertEqual(context.period_analyzed.requested_end_date, date(2025, 1, 31))
        self.assertIsNone(context.period_analyzed.observed_start_date)
        self.assertIsNone(context.period_analyzed.observed_end_date)
        self.assertEqual(context.sources_used.consultations, 0)
        self.assertEqual(context.sources_used.consultation_notes, 0)
        self.assertEqual(context.sources_used.sessions, 0)
        self.assertTrue(any("Aucune période analysable" in item for item in context.limitations))

    def test_end_date_includes_the_full_day_but_excludes_the_next_day(self):
        with self.session_factory() as db:
            patient_game = db.query(PatientGame).one()
            db.add_all(
                [
                    GameSession(
                        patient_game_id=patient_game.id,
                        duration_sec=30,
                        metrics={"score": 8},
                        created_at=datetime(2026, 9, 30, 23, 59),
                    ),
                    GameSession(
                        patient_game_id=patient_game.id,
                        duration_sec=30,
                        metrics={"score": 9},
                        created_at=datetime(2026, 10, 1),
                    ),
                ]
            )
            db.commit()

            context = build_sql_patient_context(
                db,
                self.patient_id,
                self.current_therapist_id,
                ChatPeriod(start_date=date(2026, 9, 1), end_date=date(2026, 9, 30)),
            )

        self.assertEqual(context.sources_used.sessions, 2)
        self.assertEqual(context.period_analyzed.observed_end_date, date(2026, 9, 30))

    def test_only_allowlisted_numeric_metrics_are_summarized(self):
        with self.session_factory() as db:
            patient_game = db.query(PatientGame).one()
            db.add(
                GameSession(
                    patient_game_id=patient_game.id,
                    duration_sec=90,
                    metrics={"score": 9, "completed_rounds": "four"},
                    created_at=datetime(2026, 9, 13, 9),
                )
            )
            db.commit()

            with patch(
                "app.ai.sql_context_service.settings.AI_COMPARABLE_METRIC_KEYS",
                ["score"],
            ):
                context = build_sql_patient_context(
                    db,
                    self.patient_id,
                    self.current_therapist_id,
                    ChatPeriod(start_date=date(2026, 9, 1), end_date=date(2026, 9, 30)),
                )

        self.assertEqual(len(context.metric_summaries), 1)
        score = context.metric_summaries[0]
        self.assertEqual(score["metric_key"], "score")
        self.assertEqual(score["count"], 2)
        self.assertEqual(score["mean"], 8.0)
        self.assertEqual(score["change"], 2.0)
        self.assertEqual(score["trend"], "increasing")
        self.assertEqual(score["first_date"], date(2026, 9, 12))
        self.assertEqual(score["last_date"], date(2026, 9, 13))
        self.assertIn("completed_rounds", context.uninterpretable_metric_keys)
        self.assertEqual(context.duration_summaries[0]["mean"], 67.5)

    def test_metric_with_missing_session_value_is_not_compared(self):
        with self.session_factory() as db:
            patient_game = db.query(PatientGame).one()
            db.add(
                GameSession(
                    patient_game_id=patient_game.id,
                    duration_sec=60,
                    metrics={"completed_rounds": 2},
                    created_at=datetime(2026, 9, 13, 10),
                )
            )
            db.commit()

            with patch(
                "app.ai.sql_context_service.settings.AI_COMPARABLE_METRIC_KEYS",
                ["score"],
            ):
                context = build_sql_patient_context(
                    db,
                    self.patient_id,
                    self.current_therapist_id,
                    ChatPeriod(start_date=date(2026, 9, 1), end_date=date(2026, 9, 30)),
                )

        self.assertEqual(context.metric_summaries, [])
        self.assertIn("score", context.uninterpretable_metric_keys)

    def test_chat_response_contract_validates_backend_metadata(self):
        response = ChatResponse(
            patient_id=self.patient_id,
            period_analyzed=ChatPeriodAnalyzed(
                requested_start_date=date(2026, 9, 1),
                requested_end_date=date(2026, 9, 30),
                observed_start_date=date(2026, 9, 10),
                observed_end_date=date(2026, 9, 12),
            ),
            sources_used=ChatSourcesUsed(
                consultations=1,
                consultation_notes=1,
                sessions=1,
                sessions_with_metrics=1,
                session_events=1,
            ),
            sources=[
                ChatSourceReference(
                    source_type="consultation_note",
                    source_id=1,
                    source_date=date(2026, 9, 10),
                )
            ],
            analysis="Analyse fondée sur les données disponibles.",
            limitations=[],
        )

        payload = response.model_dump(mode="json")
        self.assertEqual(payload["period_analyzed"]["observed_start_date"], "2026-09-10")
        self.assertEqual(payload["sources_used"]["consultation_notes"], 1)
        self.assertIn("analysis", payload)
        self.assertIn("limitations", payload)

        unavailable_response = ChatResponse(
            patient_id=self.patient_id,
            period_analyzed=ChatPeriodAnalyzed(
                requested_start_date=date(2025, 1, 1),
                requested_end_date=date(2025, 1, 31),
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
            limitations=["Aucune période analysable n'a pu être établie."],
        )
        self.assertIsNone(unavailable_response.model_dump(mode="json")["analysis"])

    def test_chat_service_returns_backend_metadata_and_note_only_rag_context(self):
        question = "Résume les progrès"
        request = ChatRequest(
            patient_id=self.patient_id,
            question=question,
            conversation_id="conversation-1",
            period=ChatPeriod(
                start_date=date(2026, 9, 1),
                end_date=date(2026, 9, 30),
            ),
        )
        retrieved_note = {
            "note_id": 1,
            "consultation_id": 1,
            "consultation_date": date(2026, 9, 10),
            "text": "Observation retrouvée par le RAG",
        }
        with (
            patch(
                "app.ai.chat_service.retrieve_consultation_notes",
                return_value=[retrieved_note],
            ),
            patch(
                "app.ai.chat_service.generate_analysis",
                return_value="Synthèse factuelle.",
            ) as generate_analysis,
            patch("app.ai.chat_service.settings.AI_EMBEDDING_MODEL", "test-embedding-model"),
            patch("app.ai.chat_service.is_vector_store_available", return_value=True),
            self.session_factory() as db,
        ):
            response = answer_chat(
                db,
                request,
                self.current_therapist_id,
            )

        self.assertEqual(response.analysis, "Synthèse factuelle.")
        self.assertEqual(response.conversation_id, "conversation-1")
        self.assertEqual(response.sources_used.consultation_notes, 1)
        self.assertEqual(response.period_analyzed.observed_start_date, date(2026, 9, 10))
        self.assertEqual(response.period_analyzed.observed_end_date, date(2026, 9, 12))
        self.assertTrue(any(source.source_type == "consultation_note" for source in response.sources))
        system_prompt, serialized_context = generate_analysis.call_args.args
        self.assertIn("ne pose aucun diagnostic", system_prompt.lower())
        self.assertNotIn("diagnosis", serialized_context.lower())
        self.assertNotIn("observation retrouvée", serialized_context.lower().split("consultation_note_passages")[0])
        self.assertIn("Observation retrouvée par le RAG", serialized_context)
        self.assertNotIn("period_analyzed", serialized_context)
        self.assertNotIn("sources_used", serialized_context)
        self.assertNotIn('"metrics"', serialized_context)
        self.assertNotIn('"duration_sec"', serialized_context)

    def test_sql_only_mode_uses_notes_and_reports_semantic_search_unavailable(self):
        request = ChatRequest(
            patient_id=self.patient_id,
            question="Résume les observations",
            period=ChatPeriod(
                start_date=date(2026, 9, 1),
                end_date=date(2026, 9, 30),
            ),
        )
        with (
            patch(
                "app.ai.chat_service.is_vector_store_available",
                return_value=False,
            ),
            patch(
                "app.ai.chat_service.retrieve_consultation_notes",
            ) as retrieve_rag,
            patch(
                "app.ai.chat_service.generate_analysis",
                return_value="Analyse SQL-only.",
            ) as generate_analysis,
            self.session_factory() as db,
        ):
            response = answer_chat(
                db,
                request,
                self.current_therapist_id,
            )

        self.assertEqual(response.analysis, "Analyse SQL-only.")
        self.assertEqual(response.sources_used.consultation_notes, 1)
        self.assertIn(
            "La recherche sémantique sur les notes n'est pas disponible.",
            response.limitations,
        )
        retrieve_rag.assert_not_called()
        _, serialized_context = generate_analysis.call_args.args
        self.assertIn("Observation text", serialized_context)
        self.assertNotIn("diagnosis", serialized_context.lower())

    def test_chat_service_returns_null_analysis_when_no_evidence_exists(self):
        request = ChatRequest(
            patient_id=self.patient_id,
            question="Résume le patient",
            period=ChatPeriod(
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 31),
            ),
        )
        with (
            patch("app.ai.chat_service.generate_analysis") as generate_analysis,
            self.session_factory() as db,
        ):
            response = answer_chat(
                db,
                request,
                self.current_therapist_id,
            )

        self.assertIsNone(response.analysis)
        self.assertEqual(response.sources, [])
        self.assertIsNone(response.period_analyzed.observed_start_date)
        self.assertTrue(response.limitations)
        generate_analysis.assert_not_called()

    def test_note_embeddings_are_reused_until_note_text_changes(self):
        embedder = Mock(side_effect=lambda texts: [[0.1, 0.2] for _ in texts])
        with self.session_factory() as db:
            count = index_patient_consultation_notes(
                db,
                self.patient_id,
                self.current_therapist_id,
                None,
                "test-embedding-model",
                embedder,
            )
            self.assertEqual(count, 1)
            self.assertEqual(embedder.call_count, 1)

            index_patient_consultation_notes(
                db,
                self.patient_id,
                self.current_therapist_id,
                None,
                "test-embedding-model",
                embedder,
            )
            self.assertEqual(embedder.call_count, 1)

            note = db.query(ConsultationNote).one()
            note.note = "Observation mise à jour"
            db.commit()

            index_patient_consultation_notes(
                db,
                self.patient_id,
                self.current_therapist_id,
                None,
                "test-embedding-model",
                embedder,
            )

        self.assertEqual(embedder.call_count, 2)

        with self.session_factory() as db:
            self.assertEqual(
                index_patient_consultation_notes(
                    db,
                    self.patient_id,
                    self.previous_therapist_id,
                    None,
                    "test-embedding-model",
                    embedder,
                ),
                0,
            )
            self.assertEqual(
                index_patient_consultation_notes(
                    db,
                    self.patient_id,
                    self.current_therapist_id,
                    ChatPeriod(start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)),
                    "test-embedding-model",
                    embedder,
                ),
                0,
            )
        self.assertEqual(embedder.call_count, 2)

    def test_vector_store_detection_requires_postgres_extension_and_table(self):
        db = Mock()
        db.get_bind.return_value.dialect.name = "postgresql"
        db.execute.return_value.scalar.return_value = False
        self.assertFalse(is_vector_store_available(db))
        query = str(db.execute.call_args.args[0])
        self.assertIn("pg_extension", query)
        self.assertIn("to_regclass('consultation_note_embeddings')", query)

        db.execute.return_value.scalar.return_value = True
        self.assertTrue(is_vector_store_available(db))

        non_postgres_db = Mock()
        non_postgres_db.get_bind.return_value.dialect.name = "sqlite"
        self.assertFalse(is_vector_store_available(non_postgres_db))
        non_postgres_db.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()