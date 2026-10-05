"""Small HTTP client for the KineKids FastAPI backend."""

from __future__ import annotations

import os
from typing import Any

import requests


class ApiError(RuntimeError):
    """A user-safe error returned while communicating with the API."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ApiPartialSuccessError(ApiError):
    """The patient was created, but a follow-up consultation was not."""

    def __init__(
        self,
        patient: dict,
        message: str,
        status_code: int | None = None,
    ):
        super().__init__(message, status_code)
        self.patient = patient


def api_base_url() -> str:
    return os.getenv("KINEKIDS_API_URL", "http://127.0.0.1:8000").rstrip("/")


def api_mode_enabled() -> bool:
    return os.getenv("KINEKIDS_DATA_SOURCE", "csv").strip().lower() == "api"


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
        response = requests.request(
            method,
            f"{api_base_url()}{path}",
            json=payload,
            headers=headers,
            timeout=(3.05, 15),
        )
    except requests.Timeout as exc:
        raise ApiError("L’API ne répond pas dans le délai prévu.") from exc
    except requests.ConnectionError as exc:
        raise ApiError(
            f"Impossible de joindre l’API ({api_base_url()}). Vérifiez qu’elle est démarrée."
        ) from exc
    except requests.RequestException as exc:
        raise ApiError("Erreur réseau lors de l’appel à l’API.") from exc

    if not response.ok:
        try:
            body = response.json()
            detail = body.get("detail", body)
        except ValueError:
            detail = ""

        messages = {
            400: "La requête est invalide.",
            401: "Session expirée ou identifiants invalides. Reconnectez-vous.",
            403: "Vous n’êtes pas autorisé à accéder à cette donnée.",
            404: "La ressource demandée est introuvable.",
            422: "Les données envoyées ne correspondent pas au contrat de l’API.",
        }
        message = messages.get(response.status_code, f"L’API a répondu {response.status_code}.")
        if isinstance(detail, str) and detail and response.status_code in {400, 404, 422}:
            message = f"{message} Détail : {detail}"
        raise ApiError(message, response.status_code)

    if response.status_code == 204 or not response.content:
        return None

    try:
        return response.json()
    except ValueError as exc:
        raise ApiError("L’API a renvoyé une réponse JSON invalide.", response.status_code) from exc


def login(email: str, password: str) -> str:
    result = request(
        "POST",
        "/auth/login",
        payload={"email": email, "password": password},
    )
    token = result.get("access_token") if isinstance(result, dict) else None
    if not token:
        raise ApiError("La réponse de connexion ne contient pas de jeton valide.")
    return token


def get(path: str, token: str) -> Any:
    return request("GET", path, token=token)


def post(path: str, token: str, payload: dict[str, Any]) -> Any:
    return request("POST", path, token=token, payload=payload)
