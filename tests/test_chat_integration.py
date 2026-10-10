import asyncio
import json
import threading
import unittest
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.core.config import settings
from app.core.security import create_access_token
from app.ai.llm_provider import LLMProviderError
from app.database.base import Base
from app.database.database import get_db
from app.main import app
from app.models.consultation import Consultation
from app.models.consultation_note import ConsultationNote
from app.models.game import Game
from app.models.patient import Patient
from app.models.patient_game import PatientGame
from app.models.session import Session as GameSession
from app.models.session_event import SessionEvent
from app.models.user import User


class _FakeLlmServer(ThreadingHTTPServer):
	def __init__(self, server_address):
		super().__init__(server_address, _FakeLlmHandler)
		self.requests = []


class _FakeLlmHandler(BaseHTTPRequestHandler):
	def do_POST(self):
		request_size = int(self.headers.get("Content-Length", "0"))
		payload = json.loads(self.rfile.read(request_size))
		self.server.requests.append((self.path, payload))
		user_message = next(
			message["content"]
			for message in payload["messages"]
			if message["role"] == "user"
		)
		context = json.loads(user_message)
		notes = context["consultation_note_passages"]
		sessions = context["sql_data"]["sessions"]
		metric_summaries = context["sql_data"]["metric_summaries"]
		score = metric_summaries[0]["mean"] if metric_summaries else "non interprétable"
		comparison_notes = context.get("comparison_consultation_note_passages", [])
		comparison_data = context.get("comparison_sql_data")
		if comparison_data is not None:
			comparison_metrics = comparison_data["metric_summaries"]
			comparison_score = comparison_metrics[0]["mean"] if comparison_metrics else "non interprétable"
			analysis = (
				f"Comparaison intégrée: {len(notes)} note(s) vs "
				f"{len(comparison_notes)} note(s), score {score} vs {comparison_score}."
			)
		else:
			analysis = (
				f"Analyse intégrée: {len(notes)} note(s), "
				f"{len(sessions)} session(s), score SQL {score}."
			)
		body = json.dumps(
			{
				"choices": [
					{
						"message": {
							"content": analysis,
						}
					}
				]
			}
		).encode("utf-8")
		self.send_response(200)
		self.send_header("Content-Type", "application/json")
		self.send_header("Content-Length", str(len(body)))
		self.end_headers()
		self.wfile.write(body)

	def log_message(self, format, *args):
		return


async def _asgi_request(method, path, headers, body=b""):
	messages = []
	request_sent = False

	async def receive():
		nonlocal request_sent
		if not request_sent:
			request_sent = True
			return {"type": "http.request", "body": body, "more_body": False}
		return {"type": "http.disconnect"}

	async def send(message):
		messages.append(message)

	scope = {
		"type": "http",
		"asgi": {"version": "3.0", "spec_version": "2.3"},
		"http_version": "1.1",
		"method": method,
		"scheme": "http",
		"path": path,
		"raw_path": path.encode("ascii"),
		"query_string": b"",
		"root_path": "",
		"headers": headers,
		"client": ("test-client", 12345),
		"server": ("test-server", 80),
		"state": {},
	}
	await app(scope, receive, send)
	start = next(message for message in messages if message["type"] == "http.response.start")
	response_body = b"".join(
		message.get("body", b"")
		for message in messages
		if message["type"] == "http.response.body"
	)
	return start["status"], json.loads(response_body)


class ChatIntegrationTests(unittest.TestCase):
	def setUp(self):
		self.engine = create_engine(
			"sqlite://",
			connect_args={"check_same_thread": False},
			poolclass=StaticPool,
		)
		Base.metadata.create_all(self.engine)
		self.session_factory = sessionmaker(bind=self.engine)
		self.llm_server = _FakeLlmServer(("127.0.0.1", 0))
		self.llm_thread = threading.Thread(
			target=self.llm_server.serve_forever,
			daemon=True,
		)
		self.llm_thread.start()
		self.settings_patch = patch.multiple(
			settings,
			AI_LLM_BASE_URL=f"http://127.0.0.1:{self.llm_server.server_port}/v1",
			AI_LLM_API_KEY=None,
			AI_LLM_MODEL="integration-chat",
			AI_EMBEDDING_MODEL="integration-embeddings",
			AI_COMPARABLE_METRIC_KEYS=["score"],
		)
		self.settings_patch.start()
		self.patient_id, self.owner_id, self.previous_therapist_id = self._seed_data()

		def override_get_db():
			db = self.session_factory()
			try:
				yield db
			finally:
				db.close()

		app.dependency_overrides[get_db] = override_get_db

	def tearDown(self):
		app.dependency_overrides.pop(get_db, None)
		self.settings_patch.stop()
		self.llm_server.shutdown()
		self.llm_server.server_close()
		self.llm_thread.join()
		self.engine.dispose()

	def _seed_data(self):
		with self.session_factory() as db:
			owner = User(
				full_name="Ergothérapeute actuel",
				email="owner@example.test",
				password="not-used",
				role="therapist",
			)
			previous_therapist = User(
				full_name="Ancien ergothérapeute",
				email="previous@example.test",
				password="not-used",
				role="therapist",
			)
			db.add_all([owner, previous_therapist])
			db.flush()

			patient = Patient(
				first_name="Camille",
				last_name="Exemple",
				age=9,
				patient_code="SYNTH001",
				therapist_id=owner.id,
			)
			game = Game(name="Atelier des formes", slug="atelier-formes")
			db.add_all([patient, game])
			db.flush()

			consultation = Consultation(
				patient_id=patient.id,
				therapist_id=previous_therapist.id,
				consultation_date=date(2026, 8, 12),
				diagnosis="DIAGNOSIS_SENTINEL_MUST_NOT_LEAK",
			)
			patient_game = PatientGame(
				patient_id=patient.id,
				game_id=game.id,
				configuration={"difficulty": "adapted"},
			)
			db.add_all([consultation, patient_game])
			db.flush()
			db.add(
				ConsultationNote(
					consultation_id=consultation.id,
					therapist_id=previous_therapist.id,
					note=(
						"La patiente a réalisé une activité de tri de formes. "
						"Une aide verbale a été nécessaire pour maintenir la séquence."
					),
					created_at=datetime(2026, 8, 12, 15, 30),
				)
			)
			session = GameSession(
				patient_game_id=patient_game.id,
				duration_sec=95,
				metrics={"score": 7, "completed_rounds": 4},
				created_at=datetime(2026, 8, 15, 10, 0),
			)
			db.add(session)
			db.flush()
			db.add_all([
				SessionEvent(
					session_id=session.id,
					timestamp_sec=32.5,
					event_data={"event": "sequence_completed"},
				),
			])

			previous_consultation = Consultation(
				patient_id=patient.id,
				therapist_id=previous_therapist.id,
				consultation_date=date(2026, 7, 12),
				diagnosis="SECOND_DIAGNOSIS_SENTINEL_MUST_NOT_LEAK",
			)
			db.add(previous_consultation)
			db.flush()
			db.add(
				ConsultationNote(
					consultation_id=previous_consultation.id,
					therapist_id=previous_therapist.id,
					note="En juillet, la séquence a été réalisée avec un guidage fréquent.",
					created_at=datetime(2026, 7, 12, 14, 0),
				)
			)
			previous_session = GameSession(
				patient_game_id=patient_game.id,
				duration_sec=70,
				metrics={"score": 5, "completed_rounds": 3},
				created_at=datetime(2026, 7, 16, 10, 0),
			)
			db.add(previous_session)
			db.flush()
			db.add(
				SessionEvent(
					session_id=previous_session.id,
					timestamp_sec=45.0,
					event_data={"event": "sequence_completed"},
				)
			)
			db.commit()
			return patient.id, owner.id, previous_therapist.id

	def _token(self, user_id, role="therapist"):
		return create_access_token(
			{
				"user_id": user_id,
				"sub": f"user-{user_id}@example.test",
				"role": role,
			}
		)

	def _post_chat(self, body, token=None):
		headers = [(b"content-type", b"application/json")]
		if token is not None:
			headers.append((b"authorization", f"Bearer {token}".encode("ascii")))
		return asyncio.run(
			_asgi_request(
				"POST",
				"/chat",
				headers,
				json.dumps(body).encode("utf-8"),
			)
		)

	def test_chat_uses_seeded_clinical_data_in_sql_only_mode(self):
		status, response = self._post_chat(
			{
				"patient_id": self.patient_id,
				"question": "Résume les observations et les performances.",
				"conversation_id": "integration-session-1",
				"period": {
					"start_date": "2026-08-01",
					"end_date": "2026-08-31",
				},
			},
			self._token(self.owner_id),
		)

		self.assertEqual(status, 200)
		self.assertEqual(response["analysis"], "Analyse intégrée: 1 note(s), 1 session(s), score SQL 7.0.")
		self.assertEqual(response["conversation_id"], "integration-session-1")
		self.assertEqual(response["period_analyzed"]["observed_start_date"], "2026-08-12")
		self.assertEqual(response["period_analyzed"]["observed_end_date"], "2026-08-15")
		self.assertEqual(response["sources_used"]["consultations"], 1)
		self.assertEqual(response["sources_used"]["consultation_notes"], 1)
		self.assertEqual(response["sources_used"]["sessions"], 1)
		self.assertEqual(response["sources_used"]["session_events"], 1)
		self.assertIn(
			"La recherche sémantique sur les notes n'est pas disponible.",
			response["limitations"],
		)

		self.assertEqual(len(self.llm_server.requests), 1)
		path, payload = self.llm_server.requests[0]
		self.assertEqual(path, "/v1/chat/completions")
		user_message = next(
			message["content"]
			for message in payload["messages"]
			if message["role"] == "user"
		)
		context = json.loads(user_message)
		self.assertIn(
			"Une aide verbale a été nécessaire",
			context["consultation_note_passages"][0]["text"],
		)
		self.assertEqual(context["sql_data"]["metric_summaries"][0]["mean"], 7.0)
		self.assertNotIn("metrics", context["sql_data"]["sessions"][0])
		self.assertNotIn("duration_sec", context["sql_data"]["sessions"][0])
		self.assertNotIn("DIAGNOSIS_SENTINEL_MUST_NOT_LEAK", json.dumps(context))

	def test_chat_compares_two_periods_with_distinct_backend_metadata(self):
		status, response = self._post_chat(
			{
				"patient_id": self.patient_id,
				"question": "Compare ces deux périodes",
				"period": {
					"start_date": "2026-08-01",
					"end_date": "2026-08-31",
				},
				"comparison_period": {
					"start_date": "2026-07-01",
					"end_date": "2026-07-31",
				},
			},
			self._token(self.owner_id),
		)

		self.assertEqual(status, 200)
		self.assertEqual(
			response["analysis"],
			"Comparaison intégrée: 1 note(s) vs 1 note(s), score 7.0 vs 5.0.",
		)
		self.assertEqual(response["period_analyzed"]["observed_start_date"], "2026-08-12")
		self.assertEqual(response["period_analyzed"]["observed_end_date"], "2026-08-15")
		self.assertEqual(
			response["comparison_period_analyzed"]["observed_start_date"],
			"2026-07-12",
		)
		self.assertEqual(
			response["comparison_period_analyzed"]["observed_end_date"],
			"2026-07-16",
		)
		self.assertEqual(response["sources_used"]["consultations"], 2)
		self.assertEqual(response["sources_used"]["consultation_notes"], 2)
		self.assertEqual(response["sources_used"]["sessions"], 2)
		self.assertEqual(response["sources_used"]["session_events"], 2)
		self.assertEqual(len(response["sources"]), 8)
		_, payload = self.llm_server.requests[0]
		user_message = next(
			message["content"]
			for message in payload["messages"]
			if message["role"] == "user"
		)
		context = json.loads(user_message)
		self.assertEqual(len(context["comparison_consultation_note_passages"]), 1)
		self.assertNotIn("SECOND_DIAGNOSIS_SENTINEL_MUST_NOT_LEAK", json.dumps(context))

	def test_chat_rejects_non_owner_and_missing_patient_before_llm_call(self):
		body = {"patient_id": self.patient_id, "question": "Résumé"}
		status, forbidden = self._post_chat(
			body,
			self._token(self.previous_therapist_id),
		)
		self.assertEqual(status, 403)
		self.assertEqual(forbidden["detail"], "Access denied")

		status, missing = self._post_chat(
			{"patient_id": 99999, "question": "Résumé"},
			self._token(self.owner_id),
		)
		self.assertEqual(status, 404)
		self.assertEqual(missing["detail"], "Patient not found")
		self.assertEqual(self.llm_server.requests, [])

	def test_chat_requires_therapist_authentication(self):
		status, _ = self._post_chat(
			{"patient_id": self.patient_id, "question": "Résumé"},
			self._token(self.owner_id, role="patient"),
		)
		self.assertEqual(status, 403)
		self.assertEqual(self.llm_server.requests, [])

		status, _ = self._post_chat(
			{"patient_id": self.patient_id, "question": "Résumé"},
		)
		self.assertEqual(status, 401)
		self.assertEqual(self.llm_server.requests, [])

	def test_chat_returns_422_for_invalid_request_and_documents_openapi(self):
		status, _ = self._post_chat(
			{"patient_id": 1, "question": "   "},
			self._token(self.owner_id),
		)
		self.assertEqual(status, 422)

		status, _ = self._post_chat(
			{
				"patient_id": 1,
				"question": "Compare",
				"period": {"start_date": "2026-09-30", "end_date": "2026-09-01"},
			},
			self._token(self.owner_id),
		)
		self.assertEqual(status, 422)
		self.assertEqual(self.llm_server.requests, [])

		operation = app.openapi()["paths"]["/chat"]["post"]
		self.assertIn("AI Chat", operation["tags"])
		self.assertTrue(operation["security"])
		self.assertTrue({"200", "401", "403", "404", "422", "503"}.issubset(operation["responses"]))

	def test_chat_returns_503_only_when_the_llm_is_unavailable(self):
		with patch(
			"app.ai.chat_service.generate_analysis",
			side_effect=LLMProviderError("local Ollama unavailable"),
		):
			status, response = self._post_chat(
				{
					"patient_id": self.patient_id,
					"question": "Résume les observations",
				},
				self._token(self.owner_id),
			)

		self.assertEqual(status, 503)
		self.assertEqual(
			response["detail"],
			"Le service d'analyse IA est indisponible ou mal configuré.",
		)
		self.assertNotIn("sémantique", response["detail"])
		self.assertEqual(self.llm_server.requests, [])


if __name__ == "__main__":
	unittest.main()