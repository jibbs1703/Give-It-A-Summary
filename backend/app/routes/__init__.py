"""Give-It-A-Summary backend routes package."""

from fastapi import APIRouter

from app.routes.chat import router as chat_router
from app.routes.health import router as health_router
from app.routes.summarize import router as summarize_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(summarize_router, tags=["summarize"])
api_router.include_router(chat_router, tags=["chat"])
