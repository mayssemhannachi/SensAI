import uuid

from datetime import datetime
from datetime import timedelta

from app.models.activation_code import ActivationCode

from app.repositories.activation_code_repository import (
    save_activation_code
)


def create_activation_code(
    db,
    patient_id,
    therapist_id
):

    activation_code = ActivationCode(
        patient_id=patient_id,
        created_by=therapist_id,
        code="ACT-" + str(uuid.uuid4())[:8].upper()
    )

    return save_activation_code(
        db,
        activation_code
    )