"""Task: one actionable unit of work, optionally serving a Goal."""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Task(Base):
    """A unit of work the planner can schedule into a day."""

    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("priority BETWEEN 1 AND 3", name="ck_tasks_priority_range"),
        CheckConstraint(
            "estimated_minutes > 0", name="ck_tasks_estimated_minutes_positive"
        ),
        CheckConstraint(
            "status IN ('pending', 'completed', 'skipped')",
            name="ck_tasks_status_valid",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # SET NULL rather than CASCADE: retiring a goal must not delete the work
    # already logged against it, so orphaned tasks survive as goal-less.
    goal_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("goals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2, server_default="2"
    )
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )
    scheduled_for: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
