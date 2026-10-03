from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConsultationNoteCreate(BaseModel):
    consultation_id: int
    note: str


class ConsultationNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    consultation_id: int
    therapist_id: int
    note: str
    created_at: datetime