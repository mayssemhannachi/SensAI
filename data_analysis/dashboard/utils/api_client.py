"""Client HTTP minimal pour le backend FastAPI SensAI.

Le dashboard ne parle JAMAIS directement à PostgreSQL : toutes les données
« réelles » passent par l'API. Ce module ne dépend pas de Streamlit pour rester
testable ; le choix de la source (démo / backend) est géré dans ``state.py``.
"""

from __future__ import annotations

import os
from typing import Any

import requests

try:  # python-dotenv est optionnel : on lit le .env s'il est présent.
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass


DEFAULT_API_URL = "http://127.0.0.1:8000"
CONNECT_TIMEOUT = 3.05
READ_TIMEOUT = 15

_http = requests.Session()


class ApiError(RuntimeError):
    """Erreur API présentable à l'utilisateur."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ApiPartialSuccessError(ApiError):
    """Le patient a été créé mais une étape suivante (diagnostic) a échoué."""

    def __init__(self, patient: dict, message: str, status_code: int | None = None):
        super().__init__(message, status_code)
        self.patient = patient


def api_base_url() -> str:
    return os.getenv("KINEKIDS_API_URL", DEFAULT_API_URL).strip().rstrip("/")


def site_url() -> str:
    """Adresse du site SensAI (Next.js) : connexion, inscription, espace patient."""
    return os.getenv("KINEKIDS_SITE_URL", "http://localhost:3000").strip().rstrip("/")


def default_data_source() -> str:
    """Source des données : le backend (``api``) par défaut.

    ``KINEKIDS_DATA_SOURCE=demo`` active un mode hors-ligne sur les CSV synthétiques
    (utile pour développer sans backend) ; il n'est pas proposé dans l'interface.
    """
    value = os.getenv("KINEKIDS_DATA_SOURCE", "api").strip().lower()
    return "demo" if value in {"demo", "csv"} else "api"


_ERROR_MESSAGES = {
    400: "The request is invalid.",
    401: "Session expired or invalid credentials. Please sign in again.",
    403: "You are not authorized to access this data.",
    404: "The requested resource was not found.",
    422: "The data sent does not match the API contract.",
    500: "Internal backend error.",
}


def _extract_detail(response: requests.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return ""
    detail = body.get("detail", "") if isinstance(body, dict) else body
    if isinstance(detail, list):  # erreurs de validation FastAPI
        parts = []
        for item in detail:
            if isinstance(item, dict):
                location = ".".join(str(p) for p in item.get("loc", [])[1:])
                parts.append(f"{location}: {item.get('msg', '')}".strip(" :"))
        return "; ".join(p for p in parts if p)
    return str(detail) if detail else ""


def request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
) -> Any:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = _http.request(
            method,
            f"{api_base_url()}{path}",
            json=payload,
            headers=headers,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        )
    except requests.Timeout as exc:
        raise ApiError("The backend did not respond in time.") from exc
    except requests.ConnectionError as exc:
        raise ApiError(
            f"Unable to reach the backend ({api_base_url()}). "
            "Check that it is running."
        ) from exc
    except requests.RequestException as exc:
        raise ApiError("Network error while calling the backend.") from exc

    if not response.ok:
        message = _ERROR_MESSAGES.get(
            response.status_code, f"The backend responded with {response.status_code}."
        )
        detail = _extract_detail(response)
        if detail and response.status_code in {400, 404, 422}:
            message = f"{message} Details: {detail}"
        raise ApiError(message, response.status_code)

    if response.status_code == 204 or not response.content:
        return None
    try:
        return response.json()
    except ValueError as exc:
        raise ApiError(
            "The backend returned an invalid JSON response.", response.status_code
        ) from exc


def health() -> bool:
    """True si ``GET /health`` répond correctement."""
    try:
        result = request("GET", "/health")
    except ApiError:
        return False
    return isinstance(result, dict) and str(result.get("status", "")).upper() == "UP"


def login(email: str, password: str) -> str:
    if not email or not password:
        raise ApiError("Enter your email address and password.")
    try:
        result = request("POST", "/auth/login", payload={"email": email, "password": password})
    except ApiError as error:
        if error.status_code in {400, 401, 403, 422}:
            raise ApiError("Incorrect email address or password.", error.status_code) from error
        raise
    token = result.get("access_token") if isinstance(result, dict) else None
    if not token:
        raise ApiError("The sign-in response does not contain a valid token.")
    return token


def me(token: str) -> dict:
    result = request("GET", "/auth/me", token=token)
    return result if isinstance(result, dict) else {}


def get(path: str, token: str) -> Any:
    return request("GET", path, token=token)


def post(path: str, token: str, payload: dict[str, Any]) -> Any:
    return request("POST", path, token=token, payload=payload)


def put(path: str, token: str, payload: dict[str, Any]) -> Any:
    return request("PUT", path, token=token, payload=payload)
