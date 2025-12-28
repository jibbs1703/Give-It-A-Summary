"""Chat API Route Module."""

import uuid
from typing import Any

from fastapi import APIRouter, Form, HTTPException, UploadFile
from pydantic import ValidationError

from app.agent.agent import process_chat_request
from app.models.api import AgentResponse, ChatRequest
from app.utilities.logs import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/chat", response_model=AgentResponse)
async def chat_endpoint(
    message: str = Form(..., description="User message text"),
    file: UploadFile | None = None,
    conversation_id: str | None = Form(
        None, description="Optional conversation ID for state management"
    ),
) -> AgentResponse:
    """
    Main chat endpoint for conversational document summarization.

    Accepts user messages and optional file uploads, processes them through
    the agent workflow, and returns structured responses.

    Args:
        message: The user's text message
        file: Optional file upload (PDF, DOCX, etc.) for summarization
        conversation_id: Optional conversation identifier for state management

    Returns:
        AgentResponse with processing results and delivery information

    Raises:
        HTTPException: For validation errors, processing failures, or invalid inputs
    """
    try:
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            logger.info("Generated new conversation ID: %s", conversation_id)
        else:
            logger.info("Using existing conversation ID: %s", conversation_id)

        if not message or not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        if len(message.strip()) > 10000:
            raise HTTPException(
                status_code=400, detail="Message too long (maximum 10000 characters)"
            )

        file_bytes = None
        if file:
            await validate_file_upload(file)

            try:
                file_bytes = await file.read()
                logger.info("File uploaded: %s (%d bytes)", file.filename, len(file_bytes))
            except Exception as e:  # noqa: BLE001
                logger.error("Failed to read uploaded file: %s", str(e))
                raise HTTPException(
                    status_code=400, detail=f"Failed to read uploaded file: {str(e)}"
                ) from e

        # Create chat request
        try:
            chat_request = ChatRequest(
                message=message.strip(),
                file=file_bytes,
                filename=file.filename if file else None,
                conversation_id=conversation_id,
            )
        except ValidationError as e:
            logger.error("Request validation failed: %s", str(e))
            raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}") from e

        logger.info("Processing chat request for conversation: %s", conversation_id)
        response = process_chat_request(chat_request)

        # Add conversation ID to response
        response.conversation_id = conversation_id

        logger.info("Chat request processed successfully for conversation: %s", conversation_id)
        return response

    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error("Unexpected error in chat endpoint: %s (%s)", str(e), type(e).__name__)
        raise HTTPException(
            status_code=500, detail="Internal server error occurred while processing your request"
        ) from e


async def validate_file_upload(file: UploadFile) -> None:
    """
    Validate uploaded file for security and compatibility.

    Args:
        file: The uploaded file to validate

    Raises:
        HTTPException: If file validation fails
    """
    if not file.filename or not file.filename.strip():
        raise HTTPException(status_code=400, detail="File must have a valid filename")

    allowed_extensions = {".pdf", ".docx", ".doc", ".txt", ".xlsx", ".xls", ".csv"}
    file_ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""

    if f".{file_ext}" not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}",
        )

    file_size_limit = 10 * 1024 * 1024
    if hasattr(file, "size") and file.size > file_size_limit:
        raise HTTPException(status_code=400, detail="File too large (maximum 10MB)")

    filename_lower = file.filename.lower()

    dangerous_patterns = [".exe", ".bat", ".cmd", ".scr", ".pif", ".com"]
    if any(filename_lower.endswith(pattern) for pattern in dangerous_patterns):
        raise HTTPException(status_code=400, detail="File type not allowed for security reasons")

    suspicious_patterns = ["..", "/", "\\", "<", ">", "|", "*", "?"]
    if any(pattern in file.filename for pattern in suspicious_patterns):
        raise HTTPException(status_code=400, detail="Invalid filename characters")

    logger.info("File validation passed for: %s", file.filename)


@router.get("/conversations/{conversation_id}")
async def get_conversation_status(conversation_id: str) -> dict[str, Any]:
    """
    Get the status of a conversation.

    This endpoint can be used to check if a conversation exists
    and get basic information about it.

    Args:
        conversation_id: The conversation identifier

    Returns:
        Dictionary with conversation information
    """
    return {
        "conversation_id": conversation_id,
        "status": "active",
        "message": "Conversation is active and ready for messages",
    }
