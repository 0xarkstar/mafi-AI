"""Tests for the custom exception hierarchy in src/utils/errors.py."""

import pytest

from src.utils.errors import (
    APIError,
    AgentError,
    BettingError,
    ConfigError,
    GameError,
    MafiaAIError,
    PhaseError,
    StorageError,
)


# === Base Exception ===


def test_mafia_ai_error_instantiation():
    """MafiaAIError can be created with a message."""
    err = MafiaAIError("something went wrong")
    assert str(err) == "something went wrong"
    assert err.message == "something went wrong"
    assert err.hint is None


def test_mafia_ai_error_with_hint():
    """MafiaAIError stores optional hint."""
    err = MafiaAIError("bad config", hint="check your .env file")
    assert err.message == "bad config"
    assert err.hint == "check your .env file"


def test_mafia_ai_error_is_exception():
    """MafiaAIError is a proper Exception subclass."""
    with pytest.raises(MafiaAIError):
        raise MafiaAIError("test")


# === ConfigError ===


def test_config_error_is_mafia_ai_error():
    """ConfigError inherits from MafiaAIError."""
    err = ConfigError("missing key")
    assert isinstance(err, MafiaAIError)
    assert isinstance(err, Exception)
    assert err.message == "missing key"


def test_config_error_with_hint():
    """ConfigError supports hint parameter."""
    err = ConfigError("no OPENAI_API_KEY", hint="set it in .env")
    assert err.hint == "set it in .env"


def test_config_error_raises():
    """ConfigError can be raised and caught."""
    with pytest.raises(ConfigError):
        raise ConfigError("config is broken")


# === GameError ===


def test_game_error_is_mafia_ai_error():
    """GameError inherits from MafiaAIError."""
    err = GameError("invalid game state")
    assert isinstance(err, MafiaAIError)
    assert isinstance(err, GameError)


def test_game_error_raises():
    """GameError can be raised."""
    with pytest.raises(GameError):
        raise GameError("game logic failed")


# === PhaseError ===


def test_phase_error_is_game_error():
    """PhaseError inherits from GameError."""
    err = PhaseError("invalid phase transition")
    assert isinstance(err, GameError)
    assert isinstance(err, MafiaAIError)


def test_phase_error_is_caught_as_game_error():
    """PhaseError can be caught as GameError."""
    with pytest.raises(GameError):
        raise PhaseError("cannot vote during night")


def test_phase_error_with_hint():
    """PhaseError supports hint."""
    err = PhaseError("wrong phase", hint="should be DAY_VOTE")
    assert err.hint == "should be DAY_VOTE"


# === AgentError ===


def test_agent_error_is_mafia_ai_error():
    """AgentError inherits from MafiaAIError."""
    err = AgentError("agent crashed")
    assert isinstance(err, MafiaAIError)
    assert not isinstance(err, GameError)


def test_agent_error_raises():
    """AgentError can be raised."""
    with pytest.raises(AgentError):
        raise AgentError("agent failed")


# === APIError ===


def test_api_error_is_agent_error():
    """APIError inherits from AgentError."""
    err = APIError("OpenAI returned 500")
    assert isinstance(err, AgentError)
    assert isinstance(err, MafiaAIError)


def test_api_error_is_caught_as_agent_error():
    """APIError can be caught as AgentError."""
    with pytest.raises(AgentError):
        raise APIError("rate limited")


def test_api_error_with_hint():
    """APIError supports hint."""
    err = APIError("quota exceeded", hint="check billing")
    assert err.hint == "check billing"


# === BettingError ===


def test_betting_error_is_mafia_ai_error():
    """BettingError inherits from MafiaAIError."""
    err = BettingError("bet pool empty")
    assert isinstance(err, MafiaAIError)
    assert not isinstance(err, GameError)


def test_betting_error_raises():
    """BettingError can be raised."""
    with pytest.raises(BettingError):
        raise BettingError("insufficient funds")


def test_betting_error_with_hint():
    """BettingError supports hint."""
    err = BettingError("min bet not met", hint="place at least 1 USDC")
    assert err.hint == "place at least 1 USDC"


# === StorageError ===


def test_storage_error_is_mafia_ai_error():
    """StorageError inherits from MafiaAIError."""
    err = StorageError("database locked")
    assert isinstance(err, MafiaAIError)
    assert not isinstance(err, GameError)


def test_storage_error_raises():
    """StorageError can be raised and caught."""
    with pytest.raises(StorageError):
        raise StorageError("migration failed")


def test_storage_error_with_hint():
    """StorageError supports hint."""
    err = StorageError("no connection", hint="call connect() first")
    assert err.hint == "call connect() first"


# === isinstance hierarchy checks ===


def test_phase_error_full_hierarchy():
    """PhaseError → GameError → MafiaAIError → Exception."""
    err = PhaseError("test")
    assert isinstance(err, PhaseError)
    assert isinstance(err, GameError)
    assert isinstance(err, MafiaAIError)
    assert isinstance(err, Exception)


def test_api_error_full_hierarchy():
    """APIError → AgentError → MafiaAIError → Exception."""
    err = APIError("test")
    assert isinstance(err, APIError)
    assert isinstance(err, AgentError)
    assert isinstance(err, MafiaAIError)
    assert isinstance(err, Exception)


def test_errors_are_independent():
    """GameError and AgentError are siblings, not parent/child."""
    game_err = GameError("test")
    assert not isinstance(game_err, AgentError)

    agent_err = AgentError("test")
    assert not isinstance(agent_err, GameError)
