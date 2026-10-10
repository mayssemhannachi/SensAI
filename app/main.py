from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.chat_router import router as chat_router
from app.routers.auth import router as auth_router
from app.routers.consultation import router as consultation_router
from app.routers.patient import router as patient_router
from app.routers.consultation_note import router as consultation_note_router
from app.routers.activation_code import router as activation_code_router
from app.routers.patient_transfer import router as patient_transfer_router
from app.routers.game import router as game_router
from app.routers.patient_game import router as patient_game_router
from app.routers.session import router as session_router
from app.routers.session_event import router as session_event_router
from app.core.config import settings
from app.schemas.common_schema import HealthResponse

app = FastAPI(
    title="KineKids AI API",
    description="API de gestion du suivi thérapeutique, des patients et des activités KineKids AI.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Authentication", "description": "Création de compte, connexion et identité du compte authentifié."},
        {"name": "Patients", "description": "Gestion des patients associés au thérapeute authentifié."},
        {"name": "Consultations", "description": "Création des consultations et suivi clinique des patients."},
        {"name": "Consultation Notes", "description": "Notes rattachées aux consultations."},
        {"name": "Games", "description": "Catalogue des jeux thérapeutiques."},
        {"name": "Patient Games", "description": "Associations entre patients et jeux thérapeutiques."},
        {"name": "Sessions", "description": "Sessions de jeu et mesures associées."},
        {"name": "Session Events", "description": "Événements détaillés enregistrés pendant une session."},
        {"name": "Activation Codes", "description": "Codes d’activation des patients."},
        {"name": "Patient Transfers", "description": "Transfert de patient vers le thérapeute authentifié."},
        {"name": "AI Chat", "description": "Analyse des données structurées et notes thérapeutiques d’un patient."},
        {"name": "Health", "description": "État de disponibilité de l’API."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Vérifier la disponibilité de l’API",
    description="Retourne l’état de santé du service sans nécessiter d’authentification.",
    response_description="L’état du service.",
)
def health():
    return {
        "status": "UP",
        "service": "KineKids AI",
    }


app.include_router(auth_router)
app.include_router(patient_router)
app.include_router(consultation_router)
app.include_router(consultation_note_router)
app.include_router(activation_code_router)
app.include_router(patient_transfer_router)
app.include_router(game_router)
app.include_router(patient_game_router)
app.include_router(session_router)
app.include_router(
    session_event_router
)
app.include_router(chat_router)

