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

    # Lobby & Players
    lobby_timeout_seconds: int = 300  # 5 minutes
    human_turn_timeout: int = 60  # 1 minute
    moltbook_api_url: str = "https://api.moltbook.io"

    # Moltbook Identity Authentication
    moltbook_app_key: SecretStr = SecretStr("")
    moltbook_audience: str = "mafia-ai.example.com"

    # Database
    db_path: Path = Field(default=Path("data/mafia-ai.db"))

    # Logging
    log_level: str = "INFO"

    # Blockchain (optional — set blockchain_enabled=True to activate)
    blockchain_enabled: bool = False
    blockchain_rpc_url: str = "https://data-seed-prebsc-1-s1.binance.org:8545"
    blockchain_chain_id: int = 97
    blockchain_private_key: SecretStr = SecretStr("")
    blockchain_contract_address: str = ""
    blockchain_token_decimals: int = 18  # BSC USDC=18, Monad USDC=6

    # X402 Open Betting Protocol (optional)
    x402_enabled: bool = False
    x402_facilitator_url: str = "https://api.x402.unibase.com"
    x402_network: str = "eip155:97"  # BSC testnet
    x402_usdc_address: str = "0x042E4e6a56aA1680171Da5e234D9cE42CBa03E1c"
    x402_token_decimals: int = 18
    x402_pay_to: str = ""  # Server wallet receiving USDC

    # AI Spectator Commentator (optional)
    ai_spectator_enabled: bool = True

    # AI Bettor (optional)
    ai_bettor_enabled: bool = False
    ai_bettor_private_key: SecretStr = SecretStr("")
    ai_bettor_budget_usdc: float = 50.0

    # USDC Settlement (optional)
    settlement_enabled: bool = False
    settlement_private_key: SecretStr = SecretStr("")


def load_settings() -> Settings:
    """Load settings from environment."""
    return Settings()
