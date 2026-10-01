from pydantic import BaseModel


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    age: int


class PatientUpdate(BaseModel):
    first_name: str
    last_name: str
    age: int