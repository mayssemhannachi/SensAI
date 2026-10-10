from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ChatPeriod(BaseModel):
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_date_order(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date > self.end_date
        ):
            raise ValueError("start_date must be on or before end_date")
        return self


class ChatRequest(BaseModel):
    patient_id: int
    question: str
    conversation_id: str | None = None
    period: ChatPeriod | None = None


class ChatPeriodAnalyzed(BaseModel):
    requested_start_date: date | None = Field(
        description="Début de période demandé, s'il a été fourni."
    )
    requested_end_date: date | None = Field(
        description="Fin de période demandée, s'il a été fournie."
    )
    observed_start_date: date | None = Field(
        description="Date minimale des sources effectivement utilisées."
    )
    observed_end_date: date | None = Field(
        description="Date maximale des sources effectivement utilisées."
    )


class ChatSourcesUsed(BaseModel):
    consultations: int = Field(ge=0)
    consultation_notes: int = Field(ge=0)
    sessions: int = Field(ge=0)
    sessions_with_metrics: int = Field(ge=0)
    session_events: int = Field(ge=0)


class ChatSourceReference(BaseModel):
    source_type: Literal[
        "consultation",
        "consultation_note",
        "session",
        "session_event",
    ]
    source_id: int
    source_date: date


class ChatResponse(BaseModel):
    patient_id: int
    conversation_id: str | None = None
    period_analyzed: ChatPeriodAnalyzed
    sources_used: ChatSourcesUsed
    sources: list[ChatSourceReference]
    analysis: str | None = Field(
        description="Analyse rédigée par le modèle à partir des sources autorisées."
    )
    limitations: list[str] = Field(
        description="Limites calculées par le backend à partir des données disponibles."
    )