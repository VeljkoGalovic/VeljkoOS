"""Goal: a long-horizon objective that tasks can be attached to."""

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Goal(Base):
    """An objective in one domain, tracked by percentage complete."""

    __tablename__ = "goals"
    __table_args__ = (
        CheckConstraint(
            "progress_pct BETWEEN 0 AND 100", name="ck_goals_progress_pct_range"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    progress_pct: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
