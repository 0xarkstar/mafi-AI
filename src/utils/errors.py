"""Custom exception hierarchy."""


class MafiaAIError(Exception):
    """Base exception for all MafiaAI errors."""

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        self.message = message
        self.hint = hint
        super().__init__(message)


class ConfigError(MafiaAIError):
    """Configuration error."""


class GameError(MafiaAIError):
    """Game logic error."""


class PhaseError(GameError):
    """Invalid phase transition or operation."""


class AgentError(MafiaAIError):
    """Agent-related error."""


class APIError(AgentError):
    """Claude API error."""


class BettingError(MafiaAIError):
    """Betting system error."""


class StorageError(MafiaAIError):
    """Database or persistence error."""
