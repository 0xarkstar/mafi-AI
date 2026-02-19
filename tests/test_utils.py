"""Tests for utility modules: retry, logger."""

import random
from unittest.mock import AsyncMock

import openai
import pytest

from src.utils.logger import get_logger, setup_logging
from src.utils.retry import _calculate_delay, async_retry


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
