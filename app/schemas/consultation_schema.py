from datetime import date

from pydantic import BaseModel


class ConsultationCreate(BaseModel):
    patient_id: int
    consultation_date: date
    diagnosis: str | None = None