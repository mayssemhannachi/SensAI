from pydantic import BaseModel


class ConsultationNoteCreate(BaseModel):
    consultation_id: int
    note: str