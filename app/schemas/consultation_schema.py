from datetime import date

from pydantic import BaseModel, ConfigDict


class ConsultationCreate(BaseModel):
    patient_id: int
    consultation_date: date
    diagnosis: str | None = None


class ConsultationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    therapist_id: int
    consultation_date: date
    diagnosis: str | None