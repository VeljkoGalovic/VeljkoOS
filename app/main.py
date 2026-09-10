"""VeljkoOS Core API entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.database import engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Hold the connection pool for the process lifetime, then dispose it."""
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Personal operating system: goals, tasks, learning, and daily planning.",
    lifespan=lifespan,
)
app.include_router(api_router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Liveness probe. Deliberately unprefixed, per spec."""
    return {"status": "online", "system": "VeljkoOS Core"}
