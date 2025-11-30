"""Give-It-A-Summary agent models module."""

from pydantic import BaseModel


class ExtractTextInputs(BaseModel):
    """Pydantic model for text extraction inputs."""

    file_path: str
    pages: list[int] | None = None
    delimiter: str | None = ","


class SummarizeTextInputs(BaseModel):
    """Pydantic model for text summarization inputs."""

    content: str
    max_words: int = 250
    style: str = "concise"
