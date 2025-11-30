"""Give It A Summary - Summarization Utilities Module."""

import requests
from langgraph.tools import tool

from app.core.config import get_settings
from app.models.agents import SummarizeTextInputs
from app.utilities.logs import get_logger

logger = get_logger(__name__)
settings = get_settings()


def summarize_text(content: str, max_words: int = 250, style: str = "concise") -> str:
    """
    Summarize extracted text using a local Ollama Llama model.

    Args:
        content (str): Raw text to summarize.
        max_words (int): Maximum length of the summary.
        style (str): Summarization style (e.g., "concise", "detailed", "bullet").

    Returns:
        str: Summarized text.
    """
    if not content.strip():
        logger.warning("Empty content passed to summarizer.")
        return ""

    prompt = (
        f"Summarize the following text in a {style} style, "
        f"with a maximum of {max_words} words:\n\n{content}"
    )

    try:
        response = requests.post(
            settings.OLLAMA_BASE_URL,
            json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()
        summary = result.get("response", "").strip()
        logger.info(f"Generated {style} summary with max {max_words} words.")
        return summary
    except (requests.RequestException, ValueError, KeyError) as e:
        logger.error(f"Summarization failed: {e}")
        return f"[Error] Summarization failed: {e}"


@tool
def summarize_text_tool(input_args: SummarizeTextInputs) -> str:
    """Create the summarize_text tool."""
    return summarize_text(
        content=input_args.content,
        max_words=input_args.max_words,
        style=input_args.style,
    )
