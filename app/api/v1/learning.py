"""Learning session endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.learning import LearningSession
from app.schemas.learning import LearningSessionCreate, LearningSessionRead

router = APIRouter(prefix="/learning-sessions", tags=["learning"])


@router.post(
    "", response_model=LearningSessionRead, status_code=status.HTTP_201_CREATED
)
async def create_learning_session(
    payload: LearningSessionCreate,
    db: AsyncSession = Depends(get_db),
) -> LearningSession:
    """Log a completed study block."""
    record = LearningSession(**payload.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("", response_model=list[LearningSessionRead])
async def list_learning_sessions(
    db: AsyncSession = Depends(get_db),
    subject: str | None = Query(default=None, description="Exact subject match"),
) -> list[LearningSession]:
    """List logged study blocks, newest first."""
    stmt = select(LearningSession)
    if subject is not None:
        stmt = stmt.where(LearningSession.subject == subject)

    result = await db.execute(
        stmt.order_by(LearningSession.created_at.desc(), LearningSession.id.desc())
    )
    return list(result.scalars().all())
