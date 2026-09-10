"""Goal endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.goal import Goal
from app.schemas.goal import GoalCreate, GoalRead

router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
async def create_goal(
    payload: GoalCreate,
    db: AsyncSession = Depends(get_db),
) -> Goal:
    """Create a goal."""
    goal = Goal(**payload.model_dump())
    db.add(goal)
    await db.commit()
    # Refresh to pick up server-side defaults (created_at) that the INSERT
    # generated but the in-memory instance does not know about yet.
    await db.refresh(goal)
    return goal


@router.get("", response_model=list[GoalRead])
async def list_goals(db: AsyncSession = Depends(get_db)) -> list[Goal]:
    """List all goals, newest first."""
    result = await db.execute(select(Goal).order_by(Goal.created_at.desc(), Goal.id.desc()))
    return list(result.scalars().all())
