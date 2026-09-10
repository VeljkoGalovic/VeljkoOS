"""Pydantic contracts for the daily planner."""

from datetime import date

from pydantic import BaseModel, Field


class PlanRequest(BaseModel):
    """Body for POST /api/v1/planner/generate."""

    available_minutes: int = Field(ge=1, description="Total minutes on offer today")
    energy_level: int = Field(
        ge=1,
        le=5,
        description=(
            "How rested you are: 1 = depleted, 5 = peak. Caps the longest single "
            "task admitted and flips duration ordering within a priority band."
        ),
    )
    target_date: date = Field(default_factory=date.today)


class ScheduledTask(BaseModel):
    """One task admitted to the plan, in execution order."""

    order: int
    task_id: int
    description: str
    priority: int
    estimated_minutes: int
    cumulative_start_minute: int = Field(
        description="Minutes into the session at which this task starts"
    )
    goal_id: int | None
    goal_title: str | None
    goal_category: str | None
    goal_urgency: float


class DeferredTask(BaseModel):
    """A candidate that did not make the plan, and why."""

    task_id: int
    description: str
    priority: int
    estimated_minutes: int
    reason: str = Field(
        description="'exceeds_energy_capacity' or 'insufficient_time_remaining'"
    )


class PlanResponse(BaseModel):
    """The generated day plan."""

    target_date: date
    energy_level: int
    energy_profile: str
    max_task_minutes: int | None = Field(
        description="Longest single task this energy level admits; null = uncapped"
    )
    available_minutes: int
    allocated_minutes: int
    remaining_minutes: int
    utilization_pct: float
    task_count: int
    domain_focus: dict[str, int] = Field(
        description="Goal category -> count, across the scheduled tasks only"
    )
    schedule: list[ScheduledTask]
    deferred: list[DeferredTask]
