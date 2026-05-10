"""Project settings"""

from enum import StrEnum

from pydantic import Field, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(StrEnum):
    INFO = "INFO"
    DEBUG = "DEBUG"
    ERROR = "ERROR"
    WARNING = "WARNING"


class Settings(BaseSettings):
    """Settings class"""

    # Database
    database_url: str = Field(alias="DATABASE_URL")

    # Redis
    redis_url: RedisDsn = Field(alias="REDIS_URL")

    # Celery
    celery_task_serializer: str = "json"

    # Telegram bot token
    tg_channel: str = Field(alias="TG_CHANNEL")
    telegram_api_id: int = Field(alias="TELEGRAM_API_ID")
    telegram_api_hash: SecretStr = Field(alias="TELEGRAM_API_HASH")
    telegram_session_file: str = Field(alias="TELEGRAM_SESSION_FILE")

    # ChatGPT
    openai_api_key: SecretStr = Field(alias="OPENAI_API_KEY")
    openai_model: str = Field(alias="OPENAI_MODEL")
    openai_max_retries: int = 3
    openai_base_delay: float = 1.0

    # App Configuration
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: LogLevel = Field(default=LogLevel.INFO, alias="LOG_LEVEL")

    # Pydantic configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    allowed_languages: list[str] = ["en", "ru", "kz"]


settings = Settings()   # pyright: ignore [reportCallIssue]
                        # pydantic-settings populates fields from env at runtime;
                        # Pyright can't see this statically
