import io
import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from app.ai.llm_provider import LLMProviderError, embed_texts, generate_analysis
from app.core.config import Settings, settings


class LlmProviderTests(unittest.TestCase):
	def test_default_configuration_targets_local_ollama(self):
		configuration = Settings(_env_file=None, DATABASE_URL="sqlite:///:memory:")
		self.assertEqual(configuration.AI_LLM_BASE_URL, "http://localhost:11434/v1")
		self.assertEqual(configuration.AI_LLM_MODEL, "qwen2.5:7b")
		self.assertEqual(configuration.AI_EMBEDDING_MODEL, "nomic-embed-text")
		self.assertIsNone(configuration.AI_LLM_API_KEY)

	def _response(self, payload):
		response = MagicMock()
		response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
		return response

	def test_generate_analysis_uses_openai_compatible_chat_endpoint(self):
		response = self._response(
			{"choices": [{"message": {"content": "Analyse descriptive."}}]}
		)
		with (
			patch.object(settings, "AI_LLM_BASE_URL", "http://localhost:11434/v1/"),
			patch.object(settings, "AI_LLM_MODEL", "qwen2.5:7b"),
			patch("app.ai.llm_provider.urlopen", return_value=response) as urlopen,
		):
			analysis = generate_analysis("system", "user")

		self.assertEqual(analysis, "Analyse descriptive.")
		request = urlopen.call_args.args[0]
		self.assertEqual(request.full_url, "http://localhost:11434/v1/chat/completions")
		self.assertEqual(json.loads(request.data)["model"], "qwen2.5:7b")

	def test_missing_base_url_or_model_fails_without_network_call(self):
		with (
			patch.object(settings, "AI_LLM_BASE_URL", ""),
			patch("app.ai.llm_provider.urlopen") as urlopen,
			self.assertRaises(LLMProviderError),
		):
			generate_analysis("system", "user")
		urlopen.assert_not_called()

		with (
			patch.object(settings, "AI_LLM_BASE_URL", "http://localhost:11434/v1"),
			patch.object(settings, "AI_LLM_MODEL", ""),
			patch("app.ai.llm_provider.urlopen") as urlopen,
			self.assertRaises(LLMProviderError),
		):
			generate_analysis("system", "user")
		urlopen.assert_not_called()

	def test_timeout_and_http_model_errors_are_wrapped(self):
		with (
			patch.object(settings, "AI_LLM_BASE_URL", "http://localhost:11434/v1"),
			patch.object(settings, "AI_LLM_MODEL", "missing-model"),
			patch("app.ai.llm_provider.urlopen", side_effect=TimeoutError),
			self.assertRaisesRegex(LLMProviderError, "request failed"),
		):
			generate_analysis("system", "user")

		http_error = HTTPError(
			"http://localhost:11434/v1/chat/completions",
			404,
			"model not found",
			None,
			io.BytesIO(b"model not found"),
		)
		with (
			patch.object(settings, "AI_LLM_BASE_URL", "http://localhost:11434/v1"),
			patch.object(settings, "AI_LLM_MODEL", "missing-model"),
			patch("app.ai.llm_provider.urlopen", side_effect=http_error),
			self.assertRaisesRegex(LLMProviderError, "HTTP 404"),
		):
			generate_analysis("system", "user")

	def test_invalid_json_empty_and_malformed_responses_are_rejected(self):
		with (
			patch.object(settings, "AI_LLM_BASE_URL", "http://localhost:11434/v1"),
			patch.object(settings, "AI_LLM_MODEL", "qwen2.5:7b"),
			patch("app.ai.llm_provider.urlopen") as urlopen,
			self.assertRaisesRegex(LLMProviderError, "request failed"),
		):
			response = MagicMock()
			response.__enter__.return_value.read.return_value = b"not-json"
			urlopen.return_value = response
			generate_analysis("system", "user")

		for payload, message in (
			({"choices": [{"message": {"content": "  "}}]}, "empty analysis"),
			({"unexpected": True}, "invalid response"),
		):
			with (
				patch.object(settings, "AI_LLM_BASE_URL", "http://localhost:11434/v1"),
				patch.object(settings, "AI_LLM_MODEL", "qwen2.5:7b"),
				patch("app.ai.llm_provider.urlopen", return_value=self._response(payload)),
				self.assertRaisesRegex(LLMProviderError, message),
			):
				generate_analysis("system", "user")

			with (
				patch.object(settings, "AI_LLM_BASE_URL", "http://localhost:11434/v1"),
				patch.object(settings, "AI_LLM_MODEL", "qwen2.5:7b"),
				patch("app.ai.llm_provider.urlopen") as urlopen,
				self.assertRaisesRegex(LLMProviderError, "request failed"),
			):
				response = MagicMock()
				response.__enter__.return_value.read.return_value = b"\xff"
				urlopen.return_value = response
				generate_analysis("system", "user")

	def test_embeddings_validate_response_count_and_dimensions(self):
		valid_response = self._response(
			{
				"data": [
					{"index": 1, "embedding": [0.3, 0.4]},
					{"index": 0, "embedding": [0.1, 0.2]},
				]
			}
		)
		with (
			patch.object(settings, "AI_LLM_BASE_URL", "http://localhost:11434/v1"),
			patch.object(settings, "AI_EMBEDDING_MODEL", "nomic-embed-text"),
			patch("app.ai.llm_provider.urlopen", return_value=valid_response),
		):
			self.assertEqual(embed_texts(["first", "second"]), [[0.1, 0.2], [0.3, 0.4]])

		invalid_response = self._response(
			{"data": [{"index": 0, "embedding": [0.1]}, {"index": 1, "embedding": [0.2, 0.3]}]}
		)
		with (
			patch.object(settings, "AI_LLM_BASE_URL", "http://localhost:11434/v1"),
			patch.object(settings, "AI_EMBEDDING_MODEL", "nomic-embed-text"),
			patch("app.ai.llm_provider.urlopen", return_value=invalid_response),
			self.assertRaisesRegex(LLMProviderError, "inconsistent dimensions"),
		):
			embed_texts(["first", "second"])


if __name__ == "__main__":
	unittest.main()