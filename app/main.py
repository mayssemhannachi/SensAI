from fastapi import FastAPI

from app.routers.auth import router as auth_router
from app.routers.consultation import router as consultation_router
from app.routers.patient import router as patient_router
from app.routers.consultation_note import router as consultation_note_router
from app.routers.activation_code import router as activation_code_router
from app.routers.patient_transfer import router as patient_transfer_router
app = FastAPI(
    title="KineKids AI API",
    version="1.0.0",
)


@app.get("/health")
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
