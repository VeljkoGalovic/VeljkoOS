"""ORM models.

Importing this package registers every table on ``Base.metadata``, which is what
Alembic diffs against during autogenerate. Any new model must be imported here
or its table will be silently missing from migrations.
"""

from app.models.base import Base
from app.models.goal import Goal
from app.models.learning import LearningSession
from app.models.task import Task

__all__ = ["Base", "Goal", "LearningSession", "Task"]
