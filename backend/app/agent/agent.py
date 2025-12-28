"""Give-It-A-Summary agent utilities module."""

import tempfile
from pathlib import Path
from typing import Any

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

from app.models.agent import ChatMessage, SummarizeTextInputs
from app.models.api import AgentResponse, ChatRequest
from app.tools.extract import extract_text_from_file
from app.tools.summarize import summarize_text
from app.utilities.intent import parse_user_message
from app.utilities.logs import get_logger

logger = get_logger(__name__)


class AgentState(BaseModel):
    """State for the LangGraph agent workflow."""

    messages: list[ChatMessage] = []
    intent_result: dict[str, Any] = {}
    extracted_text: str = ""
    summary: str = ""
    file_path: str | None = None
    email_sent: bool = False
    summary_path: str | None = None
    error_message: str | None = None
    response: AgentResponse | None = None


def parse_intent_node(state: AgentState) -> dict[str, Any]:
    """Parse user intent from the latest message."""
    if not state.messages:
        return {"error_message": "No messages to process"}

    latest_message = state.messages[-1]
    intent_result = parse_user_message(latest_message.content)

    logger.info("Intent parsed: %s", intent_result)
    return {"intent_result": intent_result}


def check_requirements_node(state: AgentState) -> dict[str, Any]:
    """Check if we have the requirements for summarization."""
    intent = state.intent_result

    if not intent.get("is_summary_request"):
        return {"error_message": "This is not a summarization request"}

    if not state.file_path:
        return {"error_message": "No file provided for summarization"}

    return {}


def extract_text_node(state: AgentState) -> dict[str, Any]:
    """Extract text from the uploaded file."""
    if not state.file_path:
        return {"error_message": "No file path available for extraction"}

    try:
        result = extract_text_from_file(state.file_path)
        if not result.success:
            return {"error_message": f"Text extraction failed: {result.error_message}"}

        logger.info("Text extracted successfully, length: %d", len(result.content))
        return {"extracted_text": result.content}
    except (FileNotFoundError, PermissionError) as e:
        logger.error("File access error during text extraction: %s", str(e))
        return {"error_message": f"File access error: {str(e)}"}
    except (ValueError, TypeError) as e:
        logger.error("Data processing error during text extraction: %s", str(e))
        return {"error_message": f"Data processing error: {str(e)}"}


def summarize_text_node(state: AgentState) -> dict[str, Any]:
    """Generate summary from extracted text."""
    if not state.extracted_text:
        return {"error_message": "No text available for summarization"}

    intent = state.intent_result

    try:
        summary_inputs = SummarizeTextInputs(
            content=state.extracted_text,
            max_words=intent.get("word_count") or 250,
            style=intent.get("style") or "concise",
        )

        summary_result = summarize_text(summary_inputs)
        if not summary_result.success:
            return {"error_message": f"Summarization failed: {summary_result.error_message}"}

        logger.info("Summary generated successfully, length: %d", len(summary_result.summary))
        return {"summary": summary_result.summary}
    except (ValueError, TypeError) as e:
        logger.error("Input validation error during summarization: %s", str(e))
        return {"error_message": f"Input validation error: {str(e)}"}


def create_document_node(state: AgentState) -> dict[str, Any]:
    """Create a document with the summary."""
    if not state.summary:
        return {"error_message": "No summary available for document creation"}

    try:
        summary_path = f"summary_{hash(state.summary)}.md"
        logger.info("Document creation placeholder: %s", summary_path)
        return {"summary_path": summary_path}
    except (TypeError, AttributeError) as e:
        logger.error("Data type error during document creation: %s", str(e))
        return {"error_message": f"Document creation data error: {str(e)}"}


def handle_delivery_node(state: AgentState) -> dict[str, Any]:
    """Handle delivery of summary via email or UI."""
    intent = state.intent_result

    if intent.get("email"):
        logger.info("Email delivery requested for: %s", intent["email"])
        return {"email_sent": True}
    else:
        logger.info("UI delivery - summary ready for chat interface")
        return {}


def create_response_node(state: AgentState) -> dict[str, Any]:
    """Create the final response for the user."""
    if state.error_message:
        return {
            "response": AgentResponse(
                message=f"I encountered an error: {state.error_message}", success=False
            )
        }

    intent = state.intent_result
    delivery_method = "email" if intent.get("email") else "chat interface"

    response_message = (
        f"I've successfully summarized your document and delivered it via {delivery_method}."
    )

    if state.summary:
        response_message += f"\n\nSummary preview: {state.summary[:200]}..."

    return {
        "response": AgentResponse(
            message=response_message, success=True, summary_path=state.summary_path
        )
    }


def create_agent_workflow() -> StateGraph:
    """Create the LangGraph workflow for the summarization agent."""
    workflow = StateGraph(AgentState)

    workflow.add_node("parse_intent", parse_intent_node)
    workflow.add_node("check_requirements", check_requirements_node)
    workflow.add_node("extract_text", extract_text_node)
    workflow.add_node("summarize_text", summarize_text_node)
    workflow.add_node("create_document", create_document_node)
    workflow.add_node("handle_delivery", handle_delivery_node)
    workflow.add_node("create_response", create_response_node)

    workflow.add_edge(START, "parse_intent")
    workflow.add_edge("parse_intent", "check_requirements")

    workflow.add_conditional_edges(
        "check_requirements",
        lambda state: "extract_text" if not state.error_message else "create_response",
        {"extract_text": "extract_text", "create_response": "create_response"},
    )

    workflow.add_edge("extract_text", "summarize_text")
    workflow.add_edge("summarize_text", "create_document")
    workflow.add_edge("create_document", "handle_delivery")
    workflow.add_edge("handle_delivery", "create_response")
    workflow.add_edge("create_response", END)

    return workflow


def process_chat_request(request: ChatRequest) -> AgentResponse:
    """
    Process a chat request through the agent workflow.

    Args:
        request: The chat request with message and optional file

    Returns:
        AgentResponse with the result
    """
    initial_state = AgentState()

    chat_message = ChatMessage(role="user", content=request.message, file_path=None)
    initial_state.messages = [chat_message]

    if request.file:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(request.file)
                temp_file_path = temp_file.name

            initial_state.file_path = temp_file_path
            chat_message.file_path = temp_file_path

            logger.info("File saved to temporary location: %s", temp_file_path)
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to save uploaded file: %s", str(e))
            return AgentResponse(message="Failed to process uploaded file", success=False)

    workflow = create_agent_workflow()
    app = workflow.compile()

    try:
        final_state = app.invoke(initial_state)

        if initial_state.file_path and Path(initial_state.file_path).exists():
            Path(initial_state.file_path).unlink()
            logger.info("Cleaned up temporary file: %s", initial_state.file_path)

        if hasattr(final_state, "response"):
            return final_state.response
        else:
            return AgentResponse(
                message="Processing completed but no response generated", success=False
            )

    except Exception as e:  # noqa: BLE001
        logger.error("Agent workflow execution failed: %s (%s)", str(e), type(e).__name__)

        if initial_state.file_path and Path(initial_state.file_path).exists():
            Path(initial_state.file_path).unlink()
            logger.info("Cleaned up temporary file: %s", initial_state.file_path)

        return AgentResponse(message=f"Processing failed: {str(e)}", success=False)
