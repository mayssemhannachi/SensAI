from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    age: int


class PatientUpdate(BaseModel):
    first_name: str
    last_name: str
    age: int


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    age: int
    patient_code: str
    therapist_id: int
    created_at: datetime
    # Renseigné quand le patient a activé son compte avec le code du thérapeute.
    user_id: int | None = None


class PatientDeleteResponse(BaseModel):
    message: str
    patient_id: int