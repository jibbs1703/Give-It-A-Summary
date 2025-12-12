"""Give-It-A-Summary backend core configuration module."""

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """
    Application settings for the Give-It-A-Summary backend.

    Settings can be loaded from environment variables or .env file.

    """

    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".txt", ".xlsx", ".xls", ".csv"}
    APP_API_PREFIX: str = "/api/v1"
    APP_DESCRIPTION: str = "AI powered academic paper summarization service."
    APP_NAME: str = "Give It A Summary"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:8B")

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
