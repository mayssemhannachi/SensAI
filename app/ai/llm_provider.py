import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings


class LLMProviderError(RuntimeError):
	pass


def _post(endpoint: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
	if not settings.AI_LLM_BASE_URL:
		raise LLMProviderError("AI_LLM_BASE_URL is not configured")
	base_url = settings.AI_LLM_BASE_URL.rstrip("/")
	request = Request(
		f"{base_url}/{endpoint}",
		data=json.dumps(payload).encode("utf-8"),
		headers={
			"Content-Type": "application/json",
			**(
				{"Authorization": f"Bearer {settings.AI_LLM_API_KEY}"}
				if settings.AI_LLM_API_KEY
				else {}
			),
		},
		method="POST",
	)
	try:
		with urlopen(request, timeout=timeout) as response:
			return json.loads(response.read().decode("utf-8"))
	except HTTPError as error:
		raise LLMProviderError(
			f"LLM service returned HTTP {error.code}"
		) from error
	except (
		URLError,
		TimeoutError,
		OSError,
		UnicodeDecodeError,
		json.JSONDecodeError,
	) as error:
		raise LLMProviderError("LLM service request failed") from error


def generate_analysis(system_prompt: str, user_prompt: str) -> str:
	if not settings.AI_LLM_MODEL:
		raise LLMProviderError("AI_LLM_MODEL is not configured")
	response = _post(
		"chat/completions",
		{
			"model": settings.AI_LLM_MODEL,
			"temperature": 0,
			"messages": [
				{"role": "system", "content": system_prompt},
				{"role": "user", "content": user_prompt},
			],
		},
		settings.AI_LLM_TIMEOUT_SECONDS,
	)
	try:
		content = response["choices"][0]["message"]["content"]
	except (KeyError, IndexError, TypeError) as error:
		raise LLMProviderError("LLM service returned an invalid response") from error
	if not isinstance(content, str) or not content.strip():
		raise LLMProviderError("LLM service returned an empty analysis")
	return content.strip()


def embed_texts(texts: list[str]) -> list[list[float]]:
	if not settings.AI_EMBEDDING_MODEL:
		raise LLMProviderError("AI_EMBEDDING_MODEL is not configured")
	if not texts:
		return []
	response = _post(
		"embeddings",
		{"model": settings.AI_EMBEDDING_MODEL, "input": texts},
		settings.AI_EMBEDDING_TIMEOUT_SECONDS,
	)
	try:
		items = sorted(response["data"], key=lambda item: item["index"])
		embeddings = [
			[float(value) for value in item["embedding"]]
			for item in items
		]
	except (KeyError, TypeError, ValueError) as error:
		raise LLMProviderError("Embedding service returned invalid vectors") from error
	if len(embeddings) != len(texts) or any(not vector for vector in embeddings):
		raise LLMProviderError("Embedding service returned an unexpected vector count")
	if len({len(vector) for vector in embeddings}) != 1:
		raise LLMProviderError("Embedding service returned inconsistent dimensions")
	return embeddings
