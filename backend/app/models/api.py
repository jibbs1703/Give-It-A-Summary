"""API models for request/response handling."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Pydantic model for chat API requests."""

    message: str
    file: bytes | None = None
    filename: str | None = None
    conversation_id: str | None = None


class AgentResponse(BaseModel):
    """Pydantic model for agent API responses."""

    message: str
    success: bool
    summary: str | None = None
    summary_docx_b64: str | None = None
    summary_path: str | None = None
    email_sent: bool = False
    detected_email: str | None = None
    conversation_id: str | None = None
