"""Summarize Route Module — direct file-to-summary endpoint for the Streamlit UI."""

import asyncio
import base64
import re
import tempfile
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, UploadFile

from app.core.config import get_settings
from app.models.agent import SummarizeTextInputs
from app.models.api import AgentResponse
from app.tools.email import EmailInputs, send_summary_email
from app.tools.export import DocumentExportInputs, export_to_word_document
from app.tools.extract import extract_text_from_file
from app.tools.summarize import summarize_text
from app.utilities.intent import analyze_intent_with_llm
from app.utilities.logs import get_logger

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter()

_VALID_STYLES = {"concise", "detailed", "bullets"}
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


@router.post("/summarize", response_model=AgentResponse)
async def summarize_endpoint(  # noqa: C901
    file: UploadFile,
    style: str = Form("concise", description="Summary style: concise | detailed | bullets"),
    word_count: int = Form(300, description="Maximum words in the summary (150–2000)"),
    email: str = Form("", description="Optional recipient email for the Word document"),
    user_instruction: str = Form(
        "", description="Natural language instruction (overrides style/word_count)"
    ),
) -> AgentResponse:
    """
    Upload a document and receive an AI-generated summary.

    Supports PDF, DOCX, TXT, XLSX/XLS, and CSV files. The response contains
    the summary text and a base64-encoded Word document for download.
    Optionally emails the Word document to a specified address.
    """
    if user_instruction.strip():
        try:
            intent = await asyncio.to_thread(analyze_intent_with_llm, user_instruction)
            if intent.style:
                style = intent.style
            if intent.word_count:
                word_count = intent.word_count
            if intent.email and not email.strip():
                email = intent.email
            logger.info("Intent parsed — style=%s word_count=%s", style, word_count)
        except Exception:  # noqa: BLE001
            logger.warning("Intent parsing failed, using form defaults")

    if style not in _VALID_STYLES:
        style = "concise"

    word_count = max(150, min(2000, word_count))

    recipient_email: str | None = None
    if email and email.strip():
        if not _EMAIL_RE.match(email.strip()):
            raise HTTPException(status_code=400, detail="Invalid email address format")
        recipient_email = email.strip()

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type '{file_ext}'. "
                f"Allowed: {', '.join(sorted(settings.allowed_extensions))}"
            ),
        )

    try:
        file_bytes = await file.read()
    except Exception as e:
        logger.error("Failed to read uploaded file: %s", str(e))
        raise HTTPException(status_code=400, detail="Could not read the uploaded file") from e

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    tmp_input: str | None = None
    tmp_docx: str | None = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            tmp.write(file_bytes)
            tmp_input = tmp.name

        logger.info("Saved upload to %s (%d bytes)", tmp_input, len(file_bytes))

        extraction = await asyncio.to_thread(extract_text_from_file, tmp_input)
        if not extraction.success or not extraction.content.strip():
            return AgentResponse(
                message=f"Could not extract text from '{file.filename}'. "
                "Ensure the file is not password-protected or corrupted.",
                success=False,
            )

        logger.info("Extracted %d characters from %s", len(extraction.content), file.filename)

        summarize_inputs = SummarizeTextInputs(
            content=extraction.content,
            max_words=word_count,
            style=style,
        )
        summarization = await asyncio.to_thread(summarize_text, summarize_inputs)
        if not summarization.success:
            return AgentResponse(
                message=f"Summarization failed: {summarization.error_message}",
                success=False,
            )

        logger.info("Summary generated (%d chars)", len(summarization.summary))

        export_inputs = DocumentExportInputs(
            summary=summarization.summary,
            original_filename=file.filename,
            word_count=word_count,
            style=style,
        )
        export_result = await asyncio.to_thread(export_to_word_document, export_inputs)
        if not export_result.success:
            return AgentResponse(
                message=f"Document export failed: {export_result.error_message}",
                success=False,
            )

        tmp_docx = export_result.file_path
        logger.info("Word document created at %s", tmp_docx)

        with open(tmp_docx, "rb") as f:
            summary_docx_b64 = base64.b64encode(f.read()).decode()

        email_sent = False
        if recipient_email:
            stem = Path(file.filename).stem
            email_inputs = EmailInputs(
                recipient=recipient_email,
                subject=f"Summary of '{stem}' — Give It A Summary",
                body=(
                    f"Hi,\n\nYour summary is ready. Please find it attached.\n\n"
                    f"Preview:\n{summarization.summary[:500]}"
                    + ("..." if len(summarization.summary) > 500 else "")
                    + "\n\nRegards,\nGive It A Summary"
                ),
                attachment_path=tmp_docx,
                attachment_filename=f"{stem}_summary.docx",
            )
            email_result = send_summary_email(email_inputs)
            email_sent = email_result.success
            if not email_sent:
                logger.warning("Email delivery failed: %s", email_result.error_message)

        return AgentResponse(
            message="Summary generated successfully.",
            success=True,
            summary=summarization.summary,
            summary_docx_b64=summary_docx_b64,
            email_sent=email_sent,
            detected_email=recipient_email,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in summarize endpoint: %s (%s)", str(e), type(e).__name__)
        raise HTTPException(
            status_code=500, detail="Internal server error during summarization"
        ) from e

    finally:
        for path in (tmp_input, tmp_docx):
            if path:
                try:
                    Path(path).unlink(missing_ok=True)
                except OSError:
                    pass
