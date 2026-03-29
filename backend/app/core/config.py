"""Give-It-A-Summary backend core configuration module."""

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings for the Give-It-A-Summary backend.

    Settings can be loaded from environment variables or .env file.

    """

    load_dotenv()

    allowed_extensions: set = {".pdf", ".docx", ".txt", ".xlsx", ".xls", ".csv"}
    application_api_prefix: str = "/api/v1"
    application_description: str = "AI powered academic paper summarization service."
    application_name: str = "Give It A Summary"
    application_version: str = "1.0.0"
    application_debug_flag: bool = False

    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3:0.6b")

    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from: str = os.getenv("SMTP_FROM", "")

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get or create a cached Settings instance.

    Returns:
        Settings: Cached application settings instance.
    """
    return Settings()
