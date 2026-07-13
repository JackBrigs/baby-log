"""Configuration loading and validation."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    telegram_bot_token: str = Field(..., description="Telegram Bot API token")
    baby_log_timezone: str = Field(..., description="IANA timezone for interpreting user times")
    google_service_account_file: str = Field(
        ..., description="Path to Google Service Account JSON credentials"
    )
    google_spreadsheet_id: str = Field(..., description="Google Spreadsheet ID")
