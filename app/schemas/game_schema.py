from pydantic import BaseModel, ConfigDict


class GameCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None


class GameResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    specialty: str | None = None
