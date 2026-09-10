"""The daily planner: turns a pool of pending tasks into an ordered day plan.

Pure computation over ORM instances -- no HTTP, no session handling, no IO -- so
the ranking rules below can be reasoned about and exercised in isolation.

Three inputs decide the plan:

* **priority** dominates absolutely. A priority-1 task never sorts below a
  priority-2 task, whatever the other signals say.
* **goal urgency** breaks ties inside a priority band, pulling work toward the
  goal with the nearest deadline and the least progress.
* **energy** caps the longest single task admitted and flips duration ordering:
  rested, the long deep-work blocks go first; depleted, the quick wins do.

Energy is expressed through duration because the pinned ``Task`` schema has no
difficulty column -- duration is the only intensity signal available. A
90-minute Anki grind and 90 minutes of proof-writing are indistinguishable here.
"""

from collections import Counter
from dataclasses import dataclass
from datetime import date

from app.models.goal import Goal
from app.models.task import Task
from app.schemas.planner import DeferredTask, PlanRequest, PlanResponse, ScheduledTask

# Beyond this horizon a goal's deadline stops contributing urgency.
URGENCY_HORIZON_DAYS = 90

# Relative pull of the two urgency signals; these sum to 1.0.
URGENCY_DATE_WEIGHT = 0.6
URGENCY_PROGRESS_WEIGHT = 0.4

DEFER_ENERGY = "exceeds_energy_capacity"
DEFER_TIME = "insufficient_time_remaining"


@dataclass(frozen=True)
class EnergyProfile:
    """How one energy level shapes the day.

    ``max_task_minutes`` is the tired-user guard: any task longer than this is
    deferred rather than scheduled. ``prefer_long`` flips duration ordering
    within a priority band.
    """

    label: str
    max_task_minutes: int | None
    prefer_long: bool


ENERGY_PROFILES: dict[int, EnergyProfile] = {
    1: EnergyProfile("depleted", 30, False),
    2: EnergyProfile("low", 45, False),
    3: EnergyProfile("moderate", 90, False),
    4: EnergyProfile("good", 150, True),
    5: EnergyProfile("peak", None, True),
}


def profile_for(energy_level: int) -> EnergyProfile:
    """Resolve an energy level to its profile, clamping out-of-range input."""
    return ENERGY_PROFILES[min(max(energy_level, 1), 5)]


def goal_urgency(goal: Goal | None, today: date) -> float:
    """Score a goal's pull in [0, 1].

    Returns 0.0 for a task serving no goal, and for an already-complete goal --
    finished work exerts no pull. Otherwise blends deadline proximity with how
    much remains: an overdue or same-day target saturates the date term, while a
    target past ``URGENCY_HORIZON_DAYS`` (or absent entirely) contributes none.
    """
    if goal is None or goal.progress_pct >= 100:
        return 0.0

    if goal.target_date is None:
        date_score = 0.0
    else:
        days_left = (goal.target_date - today).days
        date_score = _clamp(1.0 - (days_left / URGENCY_HORIZON_DAYS))

    progress_score = _clamp((100 - goal.progress_pct) / 100)

    return round(
        URGENCY_DATE_WEIGHT * date_score + URGENCY_PROGRESS_WEIGHT * progress_score,
        4,
    )


def generate_plan(
    request: PlanRequest,
    tasks: list[Task],
    goals: list[Goal],
) -> PlanResponse:
    """Rank the candidate tasks and greedily fill the available minutes.

    ``tasks`` are the pending candidates for the day; ``goals`` need only cover
    the goals those tasks reference. Nothing here mutates either -- the plan is
    a projection, not a commitment.
    """
    profile = profile_for(request.energy_level)
    goals_by_id = {goal.id: goal for goal in goals}

    urgency = {
        task.id: goal_urgency(goals_by_id.get(task.goal_id), request.target_date)
        for task in tasks
    }

    def rank(task: Task) -> tuple[int, float, int]:
        # Negating urgency sorts the most urgent first under an ascending sort.
        return (
            task.priority,
            -urgency[task.id],
            -task.estimated_minutes if profile.prefer_long else task.estimated_minutes,
        )

    schedule: list[ScheduledTask] = []
    deferred: list[DeferredTask] = []
    remaining = request.available_minutes

    for task in sorted(tasks, key=rank):
        if (
            profile.max_task_minutes is not None
            and task.estimated_minutes > profile.max_task_minutes
        ):
            deferred.append(_defer(task, DEFER_ENERGY))
            continue

        if task.estimated_minutes > remaining:
            # Skip rather than break: a shorter task further down the ranking
            # can still backfill the gap this one could not fit into.
            deferred.append(_defer(task, DEFER_TIME))
            continue

        goal = goals_by_id.get(task.goal_id)
        schedule.append(
            ScheduledTask(
                order=len(schedule) + 1,
                task_id=task.id,
                description=task.description,
                priority=task.priority,
                estimated_minutes=task.estimated_minutes,
                cumulative_start_minute=request.available_minutes - remaining,
                goal_id=task.goal_id,
                goal_title=goal.title if goal is not None else None,
                goal_category=goal.category if goal is not None else None,
                goal_urgency=urgency[task.id],
            )
        )
        remaining -= task.estimated_minutes

    allocated = request.available_minutes - remaining
    focus = Counter(
        item.goal_category for item in schedule if item.goal_category is not None
    )

    return PlanResponse(
        target_date=request.target_date,
        energy_level=request.energy_level,
        energy_profile=profile.label,
        max_task_minutes=profile.max_task_minutes,
        available_minutes=request.available_minutes,
        allocated_minutes=allocated,
        remaining_minutes=remaining,
        # available_minutes is constrained ge=1, so this cannot divide by zero.
        utilization_pct=round(100 * allocated / request.available_minutes, 2),
        task_count=len(schedule),
        domain_focus=dict(focus),
        schedule=schedule,
        deferred=deferred,
    )


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return min(max(value, low), high)


def _defer(task: Task, reason: str) -> DeferredTask:
    return DeferredTask(
        task_id=task.id,
        description=task.description,
        priority=task.priority,
        estimated_minutes=task.estimated_minutes,
        reason=reason,
    )
