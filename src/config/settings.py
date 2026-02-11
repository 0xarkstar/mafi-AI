"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Claude API
    anthropic_api_key: SecretStr = SecretStr("")

    # Models
    dialogue_model: str = "claude-haiku-4-5-20251001"
    decision_model: str = "claude-sonnet-4-5-20250929"
    oddsmaker_model: str = "claude-haiku-4-5-20251001"

    # Server
    host: str = "0.0.0.0"
    port: int = 8080

    # Game
    betting_window_seconds: int = 30
    starting_chips: int = 1000

    # Database
    db_path: Path = Field(default=Path("data/mafia-ai.db"))

    # Logging
    log_level: str = "INFO"


def load_settings() -> Settings:
    """Load settings from environment."""
    return Settings()
