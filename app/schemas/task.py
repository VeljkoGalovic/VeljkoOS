"""Pydantic contracts for the Task resource."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TaskStatus = Literal["pending", "completed", "skipped"]


class TaskCreate(BaseModel):
    """Body for POST /api/v1/tasks."""

    goal_id: int | None = None
    description: str = Field(min_length=1)
    priority: int = Field(default=2, ge=1, le=3, description="1 = high, 3 = low")
    estimated_minutes: int = Field(ge=1)
    status: TaskStatus = "pending"
    scheduled_for: date | None = None


class TaskUpdate(BaseModel):
    """Body for PATCH /api/v1/tasks/{task_id}.

    Every field is optional. The route applies only the keys actually present in
    the request via ``model_dump(exclude_unset=True)``, so omitting a field
    leaves it untouched while explicitly sending ``null`` clears it.
    """

    goal_id: int | None = None
    description: str | None = Field(default=None, min_length=1)
    priority: int | None = Field(default=None, ge=1, le=3)
    estimated_minutes: int | None = Field(default=None, ge=1)
    status: TaskStatus | None = None
    scheduled_for: date | None = None


class TaskRead(BaseModel):
    """Task as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    goal_id: int | None
    description: str
    priority: int
    estimated_minutes: int
    status: str
    scheduled_for: date | None
    created_at: datetime
