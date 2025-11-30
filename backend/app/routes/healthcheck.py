"""Health check Route Module."""

from typing import Any

import httpx
from fastapi import APIRouter

from app.core.config import get_settings

settings = get_settings()

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Check the health of the backend and Ollama.

    Returns:
        dict: Health status information.
    """
    ollama_models = []
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags",
                timeout=5.0
            )
            if response.status_code == 200:
                models_data = response.json()
                for model in models_data.get("models", []):
                    ollama_models.append({
                        "name": model.get("name"),
                        "size_gb": round(model.get("size", 0) / 1_000_000_000, 2),
                    })
    except (httpx.HTTPError, httpx.TimeoutException):
        ollama_models = [{"error": "Could not connect to Ollama"}]
    
    return {
        "Backend Status": "healthy",
        "Available Ollama Models": ollama_models,
    }