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

    # OpenAI API
    openai_api_key: SecretStr = SecretStr("")

    # Models
    dialogue_model: str = "gpt-4o-mini"
    decision_model: str = "gpt-4o-mini"
    oddsmaker_model: str = "gpt-4o-mini"

    # Server
    host: str = "0.0.0.0"
    port: int = 8080

    # Game
    betting_window_seconds: int = 30
    starting_chips: int = 1000

    # Lobby & Players
    lobby_timeout_seconds: int = 300  # 5 minutes
    human_turn_timeout: int = 60  # 1 minute
    moltbook_api_url: str = "https://api.moltbook.io"

    # Database
    db_path: Path = Field(default=Path("data/mafia-ai.db"))

    # Logging
    log_level: str = "INFO"

    # Blockchain (optional — set blockchain_enabled=True to activate)
    blockchain_enabled: bool = False
    blockchain_rpc_url: str = "https://testnet-rpc.monad.xyz"
    blockchain_chain_id: int = 10143
    blockchain_private_key: SecretStr = SecretStr("")
    blockchain_contract_address: str = ""


def load_settings() -> Settings:
    """Load settings from environment."""
    return Settings()
