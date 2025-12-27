"""Internal agent models for tool processing."""

from pydantic import BaseModel


class ExtractTextInputs(BaseModel):
    """Pydantic model for text extraction inputs."""

    file_path: str
    pages: list[int] | None = None
    delimiter: str | None = ","


class SummarizeTextInputs(BaseModel):
    """Pydantic model for text summarization inputs."""

    content: str
    max_words: int = 1000
    style: str = "concise"


class ChatMessage(BaseModel):
    """Pydantic model for conversation messages."""

    role: str
    content: str
    file_path: str | None = None
    timestamp: str | None = None
