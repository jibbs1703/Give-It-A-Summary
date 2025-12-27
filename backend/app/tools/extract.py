"""Give It A Summary - Extraction Tools Module."""

import os
import tempfile
from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from langextract import extract_text
from pydantic import BaseModel, Field

from app.models.agent import ExtractTextInputs
from app.utilities.logs import get_logger

logger = get_logger(__name__)


class TextExtractionResult(BaseModel):
    """Result of text extraction operation."""

    content: str = Field(..., description="Extracted text content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extraction metadata")
    success: bool = Field(default=True, description="Whether extraction was successful")
    error_message: str | None = Field(None, description="Error message if extraction failed")


def validate_file(file_path: str) -> bool:
    """Validate that file exists and is readable."""
    if not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        return False

    if not os.path.isfile(file_path):
        logger.error(f"Path is not a file: {file_path}")
        return False

    if not os.access(file_path, os.R_OK):
        logger.error(f"File is not readable: {file_path}")
        return False

    return True


def get_file_size_mb(file_path: str) -> float:
    """Get file size in MB."""
    return os.path.getsize(file_path) / (1024 * 1024)


def extract_text_from_file(file_path: str, **kwargs) -> TextExtractionResult:
    """
    Extract text from various file formats using langextract.

    Supported formats: PDF, DOCX, TXT, XLSX, CSV, and more.

    Args:
        file_path: Path to the file to extract text from
        **kwargs: Additional arguments passed to langextract

    Returns:
        TextExtractionResult with extracted content and metadata
    """
    try:
        if not validate_file(file_path):
            return TextExtractionResult(
                content="", success=False, error_message="File validation failed"
            )

        file_size_mb = get_file_size_mb(file_path)
        if file_size_mb > 50:  # Warn for files over 50MB
            logger.warning(f"Large file detected: {file_size_mb:.2f} MB")

        file_ext = Path(file_path).suffix.lower()

        logger.info(f"Extracting text from {file_path} (format: {file_ext})")
        extracted_content = extract_text(file_path, **kwargs)

        if not extracted_content or not extracted_content.strip():
            logger.warning(f"No text content extracted from {file_path}")
            return TextExtractionResult(
                content="",
                metadata={
                    "file_path": file_path,
                    "file_size_mb": file_size_mb,
                    "file_type": file_ext,
                },
                success=False,
                error_message="No text content found in file",
            )

        cleaned_content = " ".join(extracted_content.split())

        metadata = {
            "file_path": file_path,
            "file_size_mb": file_size_mb,
            "file_type": file_ext,
            "content_length": len(cleaned_content),
            "extraction_method": "langextract",
        }

        logger.info(f"Successfully extracted {len(cleaned_content)} characters from {file_path}")

        return TextExtractionResult(content=cleaned_content, metadata=metadata, success=True)

    except OSError as e:
        error_msg = f"Text extraction failed: {str(e)}"
        logger.error(f"{error_msg} for file: {file_path}")
        return TextExtractionResult(
            content="",
            metadata={"file_path": file_path, "error_type": type(e).__name__},
            success=False,
            error_message=error_msg,
        )


def extract_text_from_bytes(file_bytes: bytes, filename: str, **kwargs) -> TextExtractionResult:
    """
    Extract text from file bytes (useful for uploaded files).

    Args:
        file_bytes: Raw file bytes
        filename: Original filename (used for format detection)
        **kwargs: Additional arguments passed to langextract

    Returns:
        TextExtractionResult with extracted content and metadata
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
            temp_file.write(file_bytes)
            temp_file_path = temp_file.name

        try:
            result = extract_text_from_file(temp_file_path, **kwargs)

            result.metadata["original_filename"] = filename
            result.metadata["temp_file_used"] = True

            return result

        finally:
            try:
                os.unlink(temp_file_path)
            except OSError as e:
                logger.warning(f"Failed to clean up temporary file {temp_file_path}: {e}")

    except OSError as e:
        error_msg = f"Text extraction from bytes failed: {str(e)}"
        logger.error(error_msg)
        return TextExtractionResult(
            content="",
            metadata={"original_filename": filename, "error_type": type(e).__name__},
            success=False,
            error_message=error_msg,
        )


@tool
def extract_text_tool(inputs: ExtractTextInputs) -> str:
    """
    LangGraph tool for text extraction.

    This tool extracts text from various file formats and returns the content
    as a string for further processing in the agent workflow.

    Args:
        inputs: ExtractTextInputs containing file path and extraction parameters

    Returns:
        Extracted text content as string, or error message if extraction fails
    """
    logger.info(f"Extract text tool called with inputs: {inputs}")

    try:
        result = extract_text_from_file(
            file_path=inputs.file_path,
        )

        if result.success:
            logger.info(f"Text extraction successful: {len(result.content)} characters extracted")
            return result.content
        else:
            error_msg = f"Text extraction failed: {result.error_message}"
            logger.error(error_msg)
            return error_msg

    except OSError as e:
        error_msg = f"Tool execution failed: {str(e)}"
        logger.error(error_msg)
        return error_msg
