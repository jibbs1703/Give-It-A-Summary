"""Give It A Summary - Email Tools Module."""

import re
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.utilities.logs import get_logger

logger = get_logger(__name__)
settings = get_settings()

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")


def extract_email_from_text(text: str) -> str | None:
    """
    Extract the first valid email address found in a plain-text string.

    Args:
        text: Any free-form string (e.g. a user chat message).

    Returns:
        The first matched email address in lower-case, or None.
    """
    match = _EMAIL_RE.search(text)
    if match:
        found = match.group(0).lower()
        logger.info("Email extracted from text: %s", found)
        return found
    return None


class EmailInputs(BaseModel):
    """Inputs for sending an email with an optional attachment."""

    recipient: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Plain-text email body")
    attachment_path: str | None = Field(None, description="Path to file to attach")
    attachment_filename: str | None = Field(None, description="Display filename for the attachment")


class EmailResult(BaseModel):
    """Result of an email send operation."""

    success: bool
    error_message: str | None = None


def send_summary_email(inputs: EmailInputs) -> EmailResult:
    """
    Send a summary email with an optional Word document attachment.

    Requires SMTP_HOST, SMTP_USERNAME, and SMTP_PASSWORD to be configured.
    Returns EmailResult(success=False) silently if SMTP is not configured.
    """
    if not all([settings.smtp_host, settings.smtp_username, settings.smtp_password]):
        logger.warning("SMTP not configured — skipping email delivery")
        return EmailResult(success=False, error_message="SMTP not configured")

    try:
        msg = MIMEMultipart()
        msg["From"] = settings.smtp_from or settings.smtp_username
        msg["To"] = inputs.recipient
        msg["Subject"] = inputs.subject
        msg.attach(MIMEText(inputs.body, "plain"))

        if inputs.attachment_path:
            attachpath = Path(inputs.attachment_path)
            if attachpath.exists():
                with open(attachpath, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                display_name = inputs.attachment_filename or attachpath.name
                part.add_header("Content-Disposition", f'attachment; filename="{display_name}"')
                msg.attach(part)
            else:
                logger.warning(
                    "Attachment not found, sending email without it: %s", inputs.attachment_path
                )

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)

        logger.info("Email sent successfully to %s", inputs.recipient)
        return EmailResult(success=True)

    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP authentication failed: {str(e)}"
        logger.error(error_msg)
        return EmailResult(success=False, error_message=error_msg)
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error: {str(e)}"
        logger.error(error_msg)
        return EmailResult(success=False, error_message=error_msg)
    except OSError as e:
        error_msg = f"Network error sending email: {str(e)}"
        logger.error(error_msg)
        return EmailResult(success=False, error_message=error_msg)
