"""Give-It-A-Summary backend routes package."""

from fastapi import APIRouter

from app.routes.healthcheck import router as healthcheckrouter

api_router = APIRouter()

api_router.include_router(healthcheckrouter, tags=["health"])
