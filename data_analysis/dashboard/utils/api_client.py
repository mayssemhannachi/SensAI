"""Client HTTP minimal pour le backend FastAPI KineKids AI.

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


def default_data_source() -> str:
    """Source par défaut lue dans l'environnement : ``demo`` ou ``api``."""
    value = os.getenv("KINEKIDS_DATA_SOURCE", "demo").strip().lower()
    return "api" if value in {"api", "backend"} else "demo"


_ERROR_MESSAGES = {
    400: "La requête est invalide.",
    401: "Session expirée ou identifiants invalides. Reconnectez-vous.",
    403: "Vous n’êtes pas autorisé à accéder à cette donnée.",
    404: "La ressource demandée est introuvable.",
    422: "Les données envoyées ne correspondent pas au contrat de l’API.",
    500: "Erreur interne du backend.",
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
                parts.append(f"{location} : {item.get('msg', '')}".strip(" :"))
        return " ; ".join(p for p in parts if p)
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
        raise ApiError("Le backend ne répond pas dans le délai prévu.") from exc
    except requests.ConnectionError as exc:
        raise ApiError(
            f"Impossible de joindre le backend ({api_base_url()}). "
            "Vérifiez qu’il est démarré."
        ) from exc
    except requests.RequestException as exc:
        raise ApiError("Erreur réseau lors de l’appel au backend.") from exc

    if not response.ok:
        message = _ERROR_MESSAGES.get(
            response.status_code, f"Le backend a répondu {response.status_code}."
        )
        detail = _extract_detail(response)
        if detail and response.status_code in {400, 404, 422}:
            message = f"{message} Détail : {detail}"
        raise ApiError(message, response.status_code)

    if response.status_code == 204 or not response.content:
        return None
    try:
        return response.json()
    except ValueError as exc:
        raise ApiError(
            "Le backend a renvoyé une réponse JSON invalide.", response.status_code
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
        raise ApiError("Renseignez l’adresse e-mail et le mot de passe.")
    try:
        result = request("POST", "/auth/login", payload={"email": email, "password": password})
    except ApiError as error:
        if error.status_code in {400, 401, 403, 422}:
            raise ApiError("Adresse e-mail ou mot de passe incorrect.", error.status_code) from error
        raise
    token = result.get("access_token") if isinstance(result, dict) else None
    if not token:
        raise ApiError("La réponse de connexion ne contient pas de jeton valide.")
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
