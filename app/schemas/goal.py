"""Pydantic contracts for the Goal resource."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class GoalCreate(BaseModel):
    """Body for POST /api/v1/goals."""

    title: str = Field(min_length=1, max_length=255)
    category: str = Field(
        min_length=1,
        max_length=50,
        description="Domain label, e.g. 'math', 'programming', 'projects'",
    )
    target_date: date | None = None
    progress_pct: int = Field(default=0, ge=0, le=100)


class GoalRead(BaseModel):
    """Goal as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    target_date: date | None
    progress_pct: int
    created_at: datetime
