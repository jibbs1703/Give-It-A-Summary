"""Give It A Summary - Summarization Tools Module."""

import re
from typing import Any

import requests
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.models.agent import SummarizeTextInputs
from app.utilities.logs import get_logger
from app.utilities.prompts import CHUNK_SUMMARIZE_PROMPT, REDUCE_PROMPT, SUMMARIZE_PROMPT

logger = get_logger(__name__)
settings = get_settings()

CHUNK_SIZE = 6_000
CHUNK_OVERLAP = 200
NUM_CTX = 8192
OLLAMA_TIMEOUT = 180.0
_TOKENS_PER_WORD = 2
_WORD_COUNT_ANNOTATION = re.compile(r"\s*[\(\[\{]?\d+\s*words?[\)\]\}]?\.?\s*$", re.IGNORECASE)


class SummarizationResult(BaseModel):
    """Result of text summarization operation."""

    summary: str = Field(..., description="Generated summary text")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Summarization metadata")
    success: bool = Field(default=True, description="Whether summarization was successful")
    error_message: str | None = Field(None, description="Error message if summarization failed")


def _chunk_text(text: str) -> list[str]:
    """
    Split text into overlapping chunks that each fit within the LLM context window.

    Chunks are split on sentence boundaries where possible ('. ') to avoid
    cutting mid-sentence. A small overlap is kept between consecutive chunks
    so context is not abruptly lost at boundaries.

    Args:
        text: Full document text to split.

    Returns:
        List of text chunks.
    """
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]

        if end < len(text):
            boundary = chunk.rfind(". ")
            if boundary != -1:
                end = start + boundary + 1
                chunk = text[start:end]

        chunks.append(chunk.strip())
        start = end - CHUNK_OVERLAP

    return [c for c in chunks if c]


def _call_ollama(prompt: str, num_predict: int = 600) -> str | None:
    """
    Send a single generation request to the Ollama API.

    Args:
        prompt: Fully formatted prompt string.

    Returns:
        The model's response text, or None on failure.

    Raises:
        requests.RequestException: On network-level errors.
    """
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "top_p": 0.9,
            "num_predict": num_predict,
            "num_ctx": NUM_CTX,
        },
    }
    response = requests.post(
        f"{settings.ollama_base_url}/api/generate",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=OLLAMA_TIMEOUT,
    )
    if response.status_code != 200:
        logger.error("Ollama returned %d: %s", response.status_code, response.text[:200])
        return None
    return response.json().get("response", "").strip() or None


def _strip_annotations(text: str) -> str:
    return _WORD_COUNT_ANNOTATION.sub("", text).rstrip()


def summarize_text(inputs: SummarizeTextInputs) -> SummarizationResult:
    """
    Summarize text using a map-reduce chunking strategy.

    For short documents (under CHUNK_SIZE chars) a single Ollama call is made
    using SUMMARIZE_PROMPT. For longer documents the content is split into
    overlapping chunks via _chunk_text; each chunk is summarised independently
    using CHUNK_SUMMARIZE_PROMPT (map), then all partial summaries are
    synthesised into one final output using REDUCE_PROMPT (reduce).

    This avoids both context-window overflow and silent content truncation by
    Ollama, ensuring the full document is always processed.

    Args:
        inputs: Summarization parameters including content, style, and max_words.

    Returns:
        SummarizationResult with the generated summary and metadata.
    """
    try:
        content = inputs.content
        num_predict = inputs.max_words * _TOKENS_PER_WORD

        if len(content) <= CHUNK_SIZE:
            logger.info("Short document — using single-pass summarization (%d chars)", len(content))
            prompt = SUMMARIZE_PROMPT.format(
                style=inputs.style, max_words=inputs.max_words, content=content
            )
            summary = _call_ollama(prompt, num_predict=num_predict)
            if not summary:
                return SummarizationResult(
                    summary="", success=False, error_message="Empty summary received from Ollama"
                )
            summary = _strip_annotations(summary)
        else:
            chunks = _chunk_text(content)
            logger.info(
                "Long document (%d chars) — map-reduce over %d chunks", len(content), len(chunks)
            )

            partial_summaries: list[str] = []
            for i, chunk in enumerate(chunks):
                logger.info("Summarizing chunk %d/%d (%d chars)", i + 1, len(chunks), len(chunk))
                prompt = CHUNK_SUMMARIZE_PROMPT.format(content=chunk)
                chunk_summary = _call_ollama(prompt, num_predict=num_predict)
                if not chunk_summary:
                    return SummarizationResult(
                        summary="",
                        success=False,
                        error_message=f"Empty response for chunk {i + 1}/{len(chunks)}",
                    )
                partial_summaries.append(chunk_summary)

            combined = "\n\n---\n\n".join(
                f"[Section {i + 1}]\n{s}" for i, s in enumerate(partial_summaries)
            )
            reduce_prompt = REDUCE_PROMPT.format(
                style=inputs.style,
                max_words=inputs.max_words,
                partial_summaries=combined,
            )
            summary = _call_ollama(reduce_prompt, num_predict=num_predict)
            if not summary:
                return SummarizationResult(
                    summary="",
                    success=False,
                    error_message="Empty response during reduce step",
                )
            summary = _strip_annotations(summary)

        metadata = {
            "word_count_requested": inputs.max_words,
            "style": inputs.style,
            "input_length": len(content),
            "summary_length": len(summary),
            "chunked": len(content) > CHUNK_SIZE,
        }

        logger.info("Summarization completed successfully, output length: %d", len(summary))
        return SummarizationResult(summary=summary, metadata=metadata, success=True)

    except requests.RequestException as e:
        error_msg = f"Network error calling Ollama API: {str(e)}"
        logger.error(error_msg)
        return SummarizationResult(summary="", success=False, error_message=error_msg)
