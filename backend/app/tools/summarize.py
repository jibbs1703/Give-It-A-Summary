"""Give It A Summary - Summarization Tools Module."""

from typing import Any

import requests
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.models.agent import SummarizeTextInputs
from app.utilities.logs import get_logger
from app.utilities.prompts import SUMMARIZE_PROMPT

logger = get_logger(__name__)
settings = get_settings()


class SummarizationResult(BaseModel):
    """Result of text summarization operation."""

    summary: str = Field(..., description="Generated summary text")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Summarization metadata")
    success: bool = Field(default=True, description="Whether summarization was successful")
    error_message: str | None = Field(None, description="Error message if summarization failed")


def summarize_text(inputs: SummarizeTextInputs) -> SummarizationResult:
    """
    Summarize text using Ollama LLM.

    Args:
        inputs: Summarization parameters

    Returns:
        SummarizationResult with the generated summary
    """
    try:
        prompt = SUMMARIZE_PROMPT.format(
            style=inputs.style, max_words=inputs.max_words, content=inputs.content
        )

        ollama_payload = {
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "top_p": 0.9, "num_predict": 1000},
        }

        logger.info(
            "Sending summarization request to Ollama for %d words, style: %s",
            inputs.max_words,
            inputs.style,
        )

        response = requests.post(
            f"{settings.ollama_base_url}/api/generate",
            json=ollama_payload,
            headers={"Content-Type": "application/json"},
            timeout=120.0,
        )

        if response.status_code != 200:
            error_msg = f"Ollama API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return SummarizationResult(summary="", success=False, error_message=error_msg)

        result_data = response.json()
        summary = result_data.get("response", "").strip()

        if not summary:
            error_msg = "Empty summary received from Ollama"
            logger.error(error_msg)
            return SummarizationResult(summary="", success=False, error_message=error_msg)

        metadata = {
            "word_count_requested": inputs.max_words,
            "style": inputs.style,
            "input_length": len(inputs.content),
            "summary_length": len(summary),
        }

        logger.info("Summarization completed successfully, output length: %d", len(summary))

        return SummarizationResult(summary=summary, metadata=metadata, success=True)

    except requests.RequestException as e:
        error_msg = f"Network error calling Ollama API: {str(e)}"
        logger.error(error_msg)
        return SummarizationResult(summary="", success=False, error_message=error_msg)
