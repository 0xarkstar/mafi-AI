"""Tests for utility modules: errors, retry, logger."""

import asyncio
import random
from unittest.mock import AsyncMock, patch

import openai
import pytest

from src.utils.errors import (
    AgentError,
    APIError,
    BettingError,
    ConfigError,
    GameError,
    MafiaAIError,
    PhaseError,
    StorageError,
)
from src.utils.logger import get_logger, setup_logging
from src.utils.retry import _calculate_delay, async_retry


class TestErrorHierarchy:
    """Tests for custom exception hierarchy."""

    def test_base_error(self):
        """Test MafiaAIError with message and hint."""
        err = MafiaAIError("test error", hint="try again")
        assert err.message == "test error"
        assert err.hint == "try again"
        assert str(err) == "test error"

    def test_base_error_no_hint(self):
        """Test MafiaAIError without hint."""
        err = MafiaAIError("simple error")
        assert err.hint is None

    def test_config_error_is_base(self):
        """Test ConfigError inherits from MafiaAIError."""
        err = ConfigError("bad config")
        assert isinstance(err, MafiaAIError)

    def test_game_error_is_base(self):
        """Test GameError inherits from MafiaAIError."""
        err = GameError("game failed")
        assert isinstance(err, MafiaAIError)

    def test_phase_error_is_game_error(self):
        """Test PhaseError inherits from GameError."""
        err = PhaseError("invalid phase")
        assert isinstance(err, GameError)
        assert isinstance(err, MafiaAIError)

    def test_agent_error_is_base(self):
        """Test AgentError inherits from MafiaAIError."""
        err = AgentError("agent crashed")
        assert isinstance(err, MafiaAIError)

    def test_api_error_is_agent_error(self):
        """Test APIError inherits from AgentError."""
        err = APIError("api failed")
        assert isinstance(err, AgentError)
        assert isinstance(err, MafiaAIError)

    def test_betting_error_is_base(self):
        """Test BettingError inherits from MafiaAIError."""
        err = BettingError("bad bet")
        assert isinstance(err, MafiaAIError)

    def test_storage_error_is_base(self):
        """Test StorageError inherits from MafiaAIError."""
        err = StorageError("db down")
        assert isinstance(err, MafiaAIError)

    def test_raise_and_catch(self):
        """Test raising and catching hierarchy."""
        with pytest.raises(MafiaAIError):
            raise PhaseError("wrong phase", hint="check state machine")


class TestRetry:
    """Tests for async_retry decorator."""

    @pytest.mark.asyncio
    async def test_succeeds_first_try(self):
        """Test function that succeeds immediately."""
        mock_fn = AsyncMock(return_value="ok")

        @async_retry(max_attempts=3, base_delay=0.01)
        async def fn():
            return await mock_fn()

        result = await fn()
        assert result == "ok"
        assert mock_fn.call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_api_error(self):
        """Test retry on OpenAI APIError."""
        mock_fn = AsyncMock(
            side_effect=[
                openai.APIConnectionError(request=None),
                "recovered",
            ]
        )

        @async_retry(max_attempts=3, base_delay=0.01)
        async def fn():
            return await mock_fn()

        result = await fn()
        assert result == "recovered"
        assert mock_fn.call_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_max_attempts(self):
        """Test that exception is raised after max attempts exhausted."""
        mock_fn = AsyncMock(
            side_effect=openai.APIConnectionError(request=None),
        )

        @async_retry(max_attempts=2, base_delay=0.01)
        async def fn():
            return await mock_fn()

        with pytest.raises(openai.APIConnectionError):
            await fn()

        assert mock_fn.call_count == 2

    @pytest.mark.asyncio
    async def test_does_not_retry_unmatched_exception(self):
        """Test that non-retryable exceptions propagate immediately."""
        mock_fn = AsyncMock(side_effect=ValueError("bad input"))

        @async_retry(max_attempts=3, base_delay=0.01)
        async def fn():
            return await mock_fn()

        with pytest.raises(ValueError, match="bad input"):
            await fn()

        assert mock_fn.call_count == 1

    def test_calculate_delay_exponential(self):
        """Test delay calculation with exponential backoff."""
        random.seed(42)
        d1 = _calculate_delay(1, 1.0, 30.0, 2.0)
        d2 = _calculate_delay(2, 1.0, 30.0, 2.0)
        d3 = _calculate_delay(3, 1.0, 30.0, 2.0)

        # Each attempt should roughly double (with small jitter)
        assert 0.9 < d1 < 1.15
        assert 1.8 < d2 < 2.25
        assert 3.6 < d3 < 4.5

    def test_calculate_delay_capped(self):
        """Test delay is capped at max_delay."""
        delay = _calculate_delay(10, 1.0, 5.0, 2.0)
        assert delay <= 5.0


class TestLogger:
    """Tests for logging setup."""

    def test_get_logger_returns_bound_logger(self):
        """Test that get_logger returns a structlog logger."""
        logger = get_logger("test_module")
        assert logger is not None

    def test_setup_logging_does_not_crash(self):
        """Test that setup_logging runs without errors."""
        setup_logging("DEBUG")
        setup_logging("INFO")
        setup_logging("WARNING")
