"""Give It A Summary - Intent Analysis Module."""

import json
import re
from typing import Any

import requests

from app.core.config import get_settings
from app.utilities.logs import get_logger
from app.utilities.prompts import NLP_PARSE_PROMPT

logger = get_logger(__name__)
settings = get_settings()


class IntentResult:
    """Result of intent analysis."""

    def __init__(
        self,
        is_summary_request: bool,
        word_count: int | None,
        style: str | None,
        email: str | None,
        confidence: float = 1.0,
        raw_response: str | None = None,
    ):
        self.is_summary_request = is_summary_request
        self.word_count = word_count
        self.style = style
        self.email = email
        self.confidence = confidence
        self.raw_response = raw_response

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for easy serialization."""
        return {
            "is_summary_request": self.is_summary_request,
            "word_count": self.word_count,
            "style": self.style,
            "email": self.email,
            "confidence": self.confidence,
            "raw_response": self.raw_response,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IntentResult":
        """Create from dictionary."""
        return cls(
            is_summary_request=data.get("is_summary_request", False),
            word_count=data.get("word_count"),
            style=data.get("style"),
            email=data.get("email"),
            confidence=data.get("confidence", 1.0),
            raw_response=data.get("raw_response"),
        )


def check_summary_intent(text: str) -> bool:
    """
    Check if text contains summarization-related keywords.

    Args:
        text: Text to analyze

    Returns:
        True if summarization keywords are found
    """
    summary_keywords = [
        "summarize",
        "summary",
        "summarization",
        "abstract",
        "overview",
        "tl;dr",
        "tldr",
        "key points",
        "main points",
        "condense",
        "shorten",
        "brief",
        "concise",
        "outline",
        "digest",
        "recap",
        "recapitulate",
    ]

    text_lower = text.lower()
    return any(keyword in text_lower for keyword in summary_keywords)


def extract_email(text: str) -> str | None:
    """
    Extract email address using regex pattern.

    Args:
        text: Text to search for email

    Returns:
        First email address found, or None
    """
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    matches = re.findall(email_pattern, text)

    if matches:
        return matches[0].lower()

    return None


def analyze_intent_with_llm(message: str) -> IntentResult:
    """
    Analyze user message using LLM for intent detection.

    Args:
        message: User message to analyze

    Returns:
        IntentResult with parsed information
    """
    prompt = NLP_PARSE_PROMPT.format(message=message)

    ollama_payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "top_p": 0.9, "num_predict": 200},
    }

    logger.info("Sending intent analysis request to Ollama at %s", settings.ollama_base_url)
    response = requests.post(
        f"{settings.ollama_base_url}/api/generate",
        json=ollama_payload,
        headers={"Content-Type": "application/json"},
        timeout=30.0,
    )

    result_data = response.json()
    llm_response = result_data.get("response", "").strip()

    logger.info("LLM response received: %s...", llm_response[:100])

    parsed_json = json.loads(llm_response)
    logger.info("Successfully parsed LLM JSON response: %s", parsed_json)

    is_summary_request = parsed_json.get("is_summary_request", "no").lower() == "yes"
    word_count_str = parsed_json.get("word_count", "default")
    word_count = int(word_count_str) if word_count_str.isdigit() else None
    style = parsed_json.get("style", "default")
    style = style if style in ["concise", "detailed", "bullets"] else None
    email = parsed_json.get("email", "none")
    email = email if email != "none" else None

    result = IntentResult(
        is_summary_request=is_summary_request,
        word_count=word_count,
        style=style,
        email=email,
        confidence=0.95,
        raw_response=llm_response,
    )

    if not result.email:
        detected_email = extract_email(message)
        if detected_email:
            result.email = detected_email
            logger.info("Email detected via regex: %s", detected_email)

    keyword_summary_detected = check_summary_intent(message)
    if keyword_summary_detected and not result.is_summary_request:
        result.is_summary_request = True
        result.confidence = 0.8
        logger.info("Summary intent detected via keywords")

    logger.info("Enhanced intent analysis completed: %s", result.to_dict())
    return result


def parse_user_message(message: str) -> dict[str, Any]:
    """
    Parse user message to extract intent information.

    Args:
        message: User message to parse

    Returns:
        Dictionary with parsed intent data
    """
    result = analyze_intent_with_llm(message)
    return result.to_dict()
