from pydantic import BaseModel


class PatientTransferRequest(BaseModel):
    patient_code: str
