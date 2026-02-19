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
    blockchain_rpc_url: str = "https://testnet-rpc.monad.xyz"
    blockchain_chain_id: int = 10143
    blockchain_private_key: SecretStr = SecretStr("")
    blockchain_contract_address: str = ""

    # X402 Open Betting Protocol (optional)
    # BSC Testnet: facilitator=api.x402.unibase.com, network=eip155:97, XUSD (18 dec)
    # Monad Testnet: facilitator=x402-facilitator.molandak.org, network=eip155:10143, USDC (6 dec)
    x402_enabled: bool = False
    x402_facilitator_url: str = "https://x402-facilitator.molandak.org"
    x402_network: str = "eip155:10143"  # Monad testnet
    x402_usdc_address: str = "0x534b2f3A21130d7a60830c2Df862319e593943A3"
    x402_token_decimals: int = 6  # USDC=6, XUSD(BSC)=18
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
