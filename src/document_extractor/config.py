from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    groq_api_key: str | None = Field(default=None, validation_alias="GROQ_API_KEY")
    groq_model: str = Field(default="qwen/qwen3.6-27b", validation_alias="GROQ_MODEL")
    max_file_size_mb: int = Field(default=10, validation_alias="MAX_FILE_SIZE_MB")
    max_pdf_pages: int = Field(default=10, validation_alias="MAX_PDF_PAGES")
    max_vision_pages: int = Field(default=5, validation_alias="MAX_VISION_PAGES")
    max_image_dimension: int = Field(default=1024, validation_alias="MAX_IMAGE_DIMENSION")
    api_timeout_seconds: int = Field(default=30, validation_alias="API_TIMEOUT_SECONDS")
    max_retries: int = Field(default=1, validation_alias="MAX_RETRIES")
    max_completion_tokens: int = Field(default=1200, validation_alias="MAX_COMPLETION_TOKENS")
    money_tolerance: float = Field(default=0.01, validation_alias="MONEY_TOLERANCE")
    text_quality_threshold: float = Field(default=0.35, validation_alias="TEXT_QUALITY_THRESHOLD")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
