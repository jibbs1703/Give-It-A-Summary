"""Give It A Summary - Backend Server Module."""

import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routes import api_router
from app.utilities.logs import get_logger

settings = get_settings()
router = APIRouter()
logger = get_logger(__name__)

_OLLAMA_READY_RETRIES = 30
_OLLAMA_RETRY_INTERVAL = 5


async def _wait_for_ollama(client: httpx.AsyncClient) -> None:
    """
    Poll the Ollama /api/tags endpoint until it responds or retries are exhausted.

    Retries up to _OLLAMA_READY_RETRIES times with _OLLAMA_RETRY_INTERVAL seconds
    between attempts. Logs progress so container startup is observable.

    Args:
        client: Shared async HTTP client.

    Raises:
        RuntimeError: If Ollama does not become reachable within the retry budget.
    """
    for attempt in range(1, _OLLAMA_READY_RETRIES + 1):
        try:
            response = await client.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                logger.info("Ollama is ready (attempt %d)", attempt)
                return
        except httpx.HTTPError:
            pass

        logger.info("Waiting for Ollama... (%d/%d)", attempt, _OLLAMA_READY_RETRIES)
        await asyncio.sleep(_OLLAMA_RETRY_INTERVAL)

    raise RuntimeError(
        f"Ollama did not become reachable after {_OLLAMA_READY_RETRIES * _OLLAMA_RETRY_INTERVAL}s"
    )


async def _ensure_model_pulled(client: httpx.AsyncClient) -> None:
    """
    Pull the configured Ollama model if it is not already present locally.

    Checks the list of available models and skips the pull when the model
    already exists, avoiding unnecessary network traffic on subsequent starts.
    The pull request uses stream=False so Ollama completes the download before
    returning.

    Args:
        client: Shared async HTTP client.

    Raises:
        RuntimeError: If the pull request fails.
    """
    response = await client.get(f"{settings.ollama_base_url}/api/tags", timeout=10.0)
    available = [m.get("name", "") for m in response.json().get("models", [])]

    if any(settings.ollama_model in name for name in available):
        logger.info("Model '%s' already available — skipping pull", settings.ollama_model)
        return

    logger.info("Pulling model '%s' from Ollama registry...", settings.ollama_model)
    pull_response = await client.post(
        f"{settings.ollama_base_url}/api/pull",
        json={"name": settings.ollama_model, "stream": False},
        timeout=600.0,
    )

    if pull_response.status_code != 200:
        raise RuntimeError(
            f"Model pull failed ({pull_response.status_code}): {pull_response.text[:200]}"
        )

    logger.info("Model '%s' pulled successfully", settings.ollama_model)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage FastAPI application lifespan events.

    On startup: waits for the Ollama service to become reachable, then ensures
    the configured model is pulled and ready before the API begins serving
    requests. This prevents summarization errors caused by a cold Ollama start.
    """
    async with httpx.AsyncClient() as client:
        await _wait_for_ollama(client)
        await _ensure_model_pulled(client)

    logger.info(
        "Startup complete — serving '%s' via %s",
        settings.ollama_model,
        settings.ollama_base_url,
    )
    yield


app = FastAPI(
    title=settings.application_name,
    version=settings.application_version,
    description=settings.application_description,
    lifespan=lifespan,
    debug=settings.application_debug_flag,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.application_api_prefix)
