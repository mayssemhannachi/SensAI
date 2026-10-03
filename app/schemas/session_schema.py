from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionCreate(BaseModel):
    patient_game_id: int
    duration_sec: int
    metrics: dict


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_game_id: int
    duration_sec: int
    metrics: dict
    created_at: datetime