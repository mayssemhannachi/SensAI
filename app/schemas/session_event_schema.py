from pydantic import BaseModel, ConfigDict


class SessionEventCreate(BaseModel):
    session_id: int
    timestamp_sec: float
    event_data: dict


class SessionEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    timestamp_sec: float
    event_data: dict