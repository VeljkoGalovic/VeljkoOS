"""LearningSession: a recorded study block with before/after confidence."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LearningSession(Base):
    """One logged study block, optionally linked to notes in an Obsidian vault."""

    __tablename__ = "learning_sessions"
    __table_args__ = (
        CheckConstraint(
            "duration_minutes > 0", name="ck_learning_sessions_duration_positive"
        ),
        CheckConstraint(
            "confidence_before IS NULL OR confidence_before BETWEEN 1 AND 10",
            name="ck_learning_sessions_confidence_before_range",
        ),
        CheckConstraint(
            "confidence_after IS NULL OR confidence_after BETWEEN 1 AND 10",
            name="ck_learning_sessions_confidence_after_range",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_before: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_after: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
