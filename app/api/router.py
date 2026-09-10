"""Aggregates the v1 resource routers under a single /api/v1 prefix."""

from fastapi import APIRouter

from app.api.v1 import goals, learning, planner, tasks

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(goals.router)
api_router.include_router(tasks.router)
api_router.include_router(learning.router)
api_router.include_router(planner.router)
