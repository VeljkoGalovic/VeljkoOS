"""Daily planner endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.goal import Goal
from app.models.task import Task
from app.schemas.planner import PlanRequest, PlanResponse
from app.services.planner_engine import generate_plan

router = APIRouter(prefix="/planner", tags=["planner"])


@router.post("/generate", response_model=PlanResponse)
async def generate(
    payload: PlanRequest,
    db: AsyncSession = Depends(get_db),
) -> PlanResponse:
    """Build the day's schedule from pending work.

    Read-only: the returned plan is a projection and does not write
    ``scheduled_for`` back onto the tasks it selects.
    """
    # Candidates are pending tasks already booked for the target date, plus
    # unscheduled priority-1 work, which should not be allowed to drift.
    result = await db.execute(
        select(Task).where(
            Task.status == "pending",
            or_(
                Task.scheduled_for == payload.target_date,
                and_(Task.scheduled_for.is_(None), Task.priority == 1),
            ),
        )
    )
    tasks = list(result.scalars().all())

    # Fetch every goal the candidates reference, complete or not, so schedule
    # entries can always be enriched with a title. The engine itself decides
    # that a finished goal contributes no urgency.
    goal_ids = {task.goal_id for task in tasks if task.goal_id is not None}
    goals: list[Goal] = []
    if goal_ids:
        found = await db.execute(select(Goal).where(Goal.id.in_(goal_ids)))
        goals = list(found.scalars().all())

    return generate_plan(payload, tasks, goals)
