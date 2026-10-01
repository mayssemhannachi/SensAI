from pydantic import BaseModel


class ActivationCodeCreate(BaseModel):
    patient_id: int
