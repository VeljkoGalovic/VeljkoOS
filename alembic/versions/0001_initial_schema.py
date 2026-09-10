"""initial schema: goals, tasks, learning_sessions

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-08

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # goals first: tasks carries a foreign key into it.
    op.create_table(
        "goals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("progress_pct", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "progress_pct BETWEEN 0 AND 100", name="ck_goals_progress_pct_range"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_goals_category"), "goals", ["category"], unique=False)

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("goal_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.Integer(), server_default="2", nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column(
            "status", sa.String(length=20), server_default="pending", nullable=False
        ),
        sa.Column("scheduled_for", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "estimated_minutes > 0", name="ck_tasks_estimated_minutes_positive"
        ),
        sa.CheckConstraint("priority BETWEEN 1 AND 3", name="ck_tasks_priority_range"),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'skipped')",
            name="ck_tasks_status_valid",
        ),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tasks_goal_id"), "tasks", ["goal_id"], unique=False)
    op.create_index(
        op.f("ix_tasks_scheduled_for"), "tasks", ["scheduled_for"], unique=False
    )
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"], unique=False)

    op.create_table(
        "learning_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("subject", sa.String(length=100), nullable=False),
        sa.Column("topic", sa.String(length=100), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("confidence_before", sa.Integer(), nullable=True),
        sa.Column("confidence_after", sa.Integer(), nullable=True),
        sa.Column("notes_ref", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "confidence_after IS NULL OR confidence_after BETWEEN 1 AND 10",
            name="ck_learning_sessions_confidence_after_range",
        ),
        sa.CheckConstraint(
            "confidence_before IS NULL OR confidence_before BETWEEN 1 AND 10",
            name="ck_learning_sessions_confidence_before_range",
        ),
        sa.CheckConstraint(
            "duration_minutes > 0", name="ck_learning_sessions_duration_positive"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_learning_sessions_subject"),
        "learning_sessions",
        ["subject"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_learning_sessions_subject"), table_name="learning_sessions")
    op.drop_table("learning_sessions")
    op.drop_index(op.f("ix_tasks_status"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_scheduled_for"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_goal_id"), table_name="tasks")
    op.drop_table("tasks")
    op.drop_index(op.f("ix_goals_category"), table_name="goals")
    op.drop_table("goals")
