"""Pydantic contracts for the LearningSession resource."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LearningSessionCreate(BaseModel):
    """Body for POST /api/v1/learning-sessions."""

    subject: str = Field(min_length=1, max_length=100)
    topic: str = Field(min_length=1, max_length=100)
    duration_minutes: int = Field(ge=1)
    confidence_before: int | None = Field(default=None, ge=1, le=10)
    confidence_after: int | None = Field(default=None, ge=1, le=10)
    notes_ref: str | None = Field(
        default=None, max_length=255, description="Obsidian vault path or URI"
    )


class LearningSessionRead(LearningSessionCreate):
    """Learning session as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
