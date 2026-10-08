from pydantic import BaseModel, ConfigDict


class PatientGameCreate(BaseModel):
    patient_id: int
    game_id: int
    configuration: dict


class PatientGameResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    game_id: int
    configuration: dict

class PatientGameUpdate(BaseModel):
    configuration: dict


class PatientGameDetail(PatientGameResponse):
    game_name: str | None = None
    game_slug: str | None = None
