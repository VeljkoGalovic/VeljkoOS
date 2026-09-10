"""Task endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.goal import Goal
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskRead, TaskStatus, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
) -> Task:
    """Create a task, optionally attached to an existing goal."""
    if payload.goal_id is not None and await db.get(Goal, payload.goal_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal {payload.goal_id} does not exist",
        )

    task = Task(**payload.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    scheduled_for: date | None = Query(
        default=None, description="Exact scheduled date, YYYY-MM-DD"
    ),
    # Aliased because the bare name `status` would shadow fastapi.status above.
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
) -> list[Task]:
    """List tasks, optionally filtered by scheduled date and/or status."""
    stmt = select(Task)
    if scheduled_for is not None:
        stmt = stmt.where(Task.scheduled_for == scheduled_for)
    if status_filter is not None:
        stmt = stmt.where(Task.status == status_filter)

    result = await db.execute(stmt.order_by(Task.priority.asc(), Task.id.asc()))
    return list(result.scalars().all())


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
) -> Task:
    """Partially update a task -- status, timing, or any other field."""
    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    # exclude_unset distinguishes "field omitted" from "field explicitly null",
    # so a PATCH can clear scheduled_for without wiping untouched columns.
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body contained no fields to update",
        )

    new_goal_id = changes.get("goal_id")
    if new_goal_id is not None and await db.get(Goal, new_goal_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal {new_goal_id} does not exist",
        )

    for field, value in changes.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    return task
