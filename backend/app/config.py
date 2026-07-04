import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Database — SQLite for local dev, PostgreSQL for production
    DATABASE_URL: str = f"sqlite+aiosqlite:///{PROJECT_ROOT / 'citadel.db'}"

    # Redis (optional for local dev — falls back to in-memory)
    REDIS_URL: str = ""

    # Resend
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "noreply@mail.citadelcloudmanagement.com"
    RESEND_FROM_NAME: str = "Citadel Cloud Management"

    # AI
    ANTHROPIC_API_KEY: str = ""

    # App
    APP_SECRET_KEY: str = "local-dev-secret-change-in-production"
    APP_ENV: str = "development"
    APP_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"

    # Rate limiting
    SEND_RATE_PER_MINUTE: int = 60
    MAX_DAILY_SENDS: int = 5000

    # Compliance
    UNSUBSCRIBE_BASE_URL: str = "http://localhost:8000/api/v1/unsubscribe"
    COMPANY_NAME: str = "Citadel Cloud Management"
    COMPANY_ADDRESS: str = "United States"

    # Upload directory
    UPLOAD_DIR: str = str(PROJECT_ROOT / "uploads")

    model_config = {"env_file": str(PROJECT_ROOT / ".env"), "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    # Render provides postgres:// URLs — SQLAlchemy needs postgresql+asyncpg://
    if s.DATABASE_URL.startswith("postgres://"):
        s.DATABASE_URL = s.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif s.DATABASE_URL.startswith("postgresql://"):
        s.DATABASE_URL = s.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    return s
