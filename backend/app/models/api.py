"""API models for request/response handling."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Pydantic model for chat API requests."""

    message: str
    file: bytes | None = None
    conversation_id: str | None = None


class AgentResponse(BaseModel):
    """Pydantic model for agent API responses."""

    message: str
    success: bool
    summary_path: str | None = None
    conversation_id: str | None = None
