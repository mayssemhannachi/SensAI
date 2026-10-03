from pydantic import BaseModel


class PatientTransferRequest(BaseModel):
    patient_code: str


class PatientTransferResponse(BaseModel):
    message: str
    new_patient_code: str
