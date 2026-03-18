from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://gramscout:changeme@postgres:5432/gramscout"
    )

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Telegram
    TELEGRAM_API_ID: Optional[str] = None
    TELEGRAM_API_HASH: Optional[str] = None

    # OpenRouter
    OPENROUTER_API_KEY: Optional[str] = None

    # App
    SECRET_KEY: str = "change-this"
    DEBUG: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    # Encryption
    ENCRYPTION_KEY: Optional[str] = None

    # Proxy
    MAX_ACCOUNTS_PER_PROXY: int = 5

    # Commenting
    DEFAULT_COMMENT_DELAY_MIN: int = 30
    DEFAULT_COMMENT_DELAY_MAX: int = 300
    MAX_CONCURRENT_WORKERS: int = 50

    # Warming
    WARMING_ACTIONS_PER_HOUR: int = 5
    WARMING_SESSION_DURATION_MIN: int = 15

    @field_validator("TELEGRAM_API_ID", mode="before")
    @classmethod
    def parse_api_id(cls, v):
        if v in ("", None):
            return None
        return str(v)

    @field_validator(
        "OPENROUTER_API_KEY", "TELEGRAM_API_HASH", "ENCRYPTION_KEY", mode="before"
    )
    @classmethod
    def empty_to_none(cls, v):
        if v == "":
            return None
        return v

    class Config:
        env_file = ".env"


settings = Settings()
