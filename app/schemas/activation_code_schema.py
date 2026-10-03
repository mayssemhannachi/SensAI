from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivationCodeCreate(BaseModel):
    patient_id: int


class ActivationCodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    created_by: int
    code: str
    is_used: bool
    created_at: datetime
    expires_at: datetime
    used_at: datetime | None
