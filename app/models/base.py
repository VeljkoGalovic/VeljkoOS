"""Shared declarative base for every ORM model."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Carries the metadata that Alembic autogenerates against."""
