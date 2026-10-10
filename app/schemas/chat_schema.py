from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


ChatQuestion = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=4000),
]
ConversationId = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=128),
]
PositiveStrictInt = Annotated[int, Field(strict=True, gt=0)]


class ChatPeriod(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_date: date | None = None
    end_date: date | None = None

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def validate_iso_date(cls, value):
        if value is None or isinstance(value, date) and not isinstance(value, datetime):
            return value
        if not isinstance(value, str):
            raise ValueError("Dates must use the ISO YYYY-MM-DD format")
        try:
            parsed = date.fromisoformat(value)
        except ValueError as error:
            raise ValueError("Dates must use the ISO YYYY-MM-DD format") from error
        if parsed.isoformat() != value:
            raise ValueError("Dates must use the ISO YYYY-MM-DD format")
        return parsed

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
    model_config = ConfigDict(extra="forbid")

    patient_id: PositiveStrictInt
    question: ChatQuestion
    conversation_id: ConversationId | None = None
    period: ChatPeriod | None = None
    comparison_period: ChatPeriod | None = None

    @model_validator(mode="after")
    def validate_comparison_period(self):
        if self.comparison_period is not None and self.period is None:
            raise ValueError("period is required when comparison_period is provided")
        return self


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
    source_id: PositiveStrictInt
    source_date: date


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: PositiveStrictInt
    conversation_id: ConversationId | None = None
    period_analyzed: ChatPeriodAnalyzed
    comparison_period_analyzed: ChatPeriodAnalyzed | None = None
    sources_used: ChatSourcesUsed
    sources: list[ChatSourceReference]
    analysis: str | None = Field(
        description="Analyse rédigée par le modèle à partir des sources autorisées."
    )
    limitations: list[str] = Field(
        description="Limites calculées par le backend à partir des données disponibles."
    )