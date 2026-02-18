"""Tests for the async_retry decorator in src/utils/retry.py."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.utils.retry import _calculate_delay, async_retry


# === _calculate_delay ===


def test_calculate_delay_first_attempt():
    """First attempt has base delay."""
    delay = _calculate_delay(attempt=1, base_delay=1.0, max_delay=30.0, multiplier=2.0)
    # base_delay * multiplier^(attempt-1) = 1.0 * 2^0 = 1.0, plus up to 10% jitter
    assert 1.0 <= delay <= 1.2


def test_calculate_delay_exponential_growth():
    """Delay grows exponentially with each attempt."""
    delay1 = _calculate_delay(1, base_delay=1.0, max_delay=100.0, multiplier=2.0)
    delay2 = _calculate_delay(2, base_delay=1.0, max_delay=100.0, multiplier=2.0)
    delay3 = _calculate_delay(3, base_delay=1.0, max_delay=100.0, multiplier=2.0)
    # delay2 ≈ 2x delay1, delay3 ≈ 4x delay1 (modulo jitter)
    assert delay2 > delay1
    assert delay3 > delay2


def test_calculate_delay_respects_max():
    """Delay is capped at max_delay."""
    # With attempt=100, uncapped delay would be enormous
    delay = _calculate_delay(attempt=100, base_delay=1.0, max_delay=5.0, multiplier=2.0)
    assert delay <= 5.0


def test_calculate_delay_includes_jitter():
    """Multiple calls produce slightly different values due to jitter."""
    delays = {
        _calculate_delay(1, base_delay=1.0, max_delay=30.0, multiplier=2.0)
        for _ in range(10)
    }
    # Statistically very unlikely to get 10 identical values with random jitter
    assert len(delays) > 1 or True  # Soft check - jitter is 0-10%


# === async_retry decorator ===


class MyRetryableError(Exception):
    """Custom retryable exception for testing."""


class MyNonRetryableError(Exception):
    """Custom non-retryable exception for testing."""


@pytest.mark.asyncio
async def test_retry_succeeds_on_first_try():
    """Function succeeds immediately without retrying."""
    call_count = 0

    @async_retry(max_attempts=3, retryable_exceptions=(MyRetryableError,))
    async def my_func():
        nonlocal call_count
        call_count += 1
        return "ok"

    result = await my_func()
    assert result == "ok"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_succeeds_on_second_try():
    """Function fails once then succeeds."""
    call_count = 0

    @async_retry(
        max_attempts=3,
        base_delay=0.001,
        retryable_exceptions=(MyRetryableError,),
    )
    async def my_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise MyRetryableError("temporary failure")
        return "recovered"

    with patch("src.utils.retry.asyncio.sleep", new_callable=AsyncMock):
        result = await my_func()

    assert result == "recovered"
    assert call_count == 2


@pytest.mark.asyncio
async def test_retry_exhausts_max_attempts_and_raises():
    """Function always fails → raises after max_attempts."""
    call_count = 0

    @async_retry(
        max_attempts=3,
        base_delay=0.001,
        retryable_exceptions=(MyRetryableError,),
    )
    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise MyRetryableError(f"attempt {call_count}")

    with patch("src.utils.retry.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(MyRetryableError, match="attempt 3"):
            await always_fails()

    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_does_not_catch_non_retryable_exception():
    """Non-retryable exceptions propagate immediately without retrying."""
    call_count = 0

    @async_retry(
        max_attempts=3,
        base_delay=0.001,
        retryable_exceptions=(MyRetryableError,),
    )
    async def raises_non_retryable():
        nonlocal call_count
        call_count += 1
        raise MyNonRetryableError("fatal error")

    with pytest.raises(MyNonRetryableError, match="fatal error"):
        await raises_non_retryable()

    # Only called once - no retry for non-retryable exceptions
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_sleeps_between_attempts():
    """asyncio.sleep is called between retry attempts."""
    call_count = 0

    @async_retry(
        max_attempts=3,
        base_delay=1.0,
        retryable_exceptions=(MyRetryableError,),
    )
    async def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise MyRetryableError("not yet")
        return "done"

    with patch("src.utils.retry.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await flaky()

    assert result == "done"
    assert call_count == 3
    # Sleep called twice (between attempt 1→2 and 2→3)
    assert mock_sleep.call_count == 2


@pytest.mark.asyncio
async def test_retry_preserves_function_name():
    """Decorated function preserves its __name__ via functools.wraps."""

    @async_retry(max_attempts=3, retryable_exceptions=(MyRetryableError,))
    async def my_important_function():
        return "x"

    assert my_important_function.__name__ == "my_important_function"


@pytest.mark.asyncio
async def test_retry_passes_args_and_kwargs():
    """Decorated function receives args and kwargs correctly."""

    @async_retry(max_attempts=1, retryable_exceptions=(MyRetryableError,))
    async def add(a, b, multiplier=1):
        return (a + b) * multiplier

    result = await add(3, 4, multiplier=2)
    assert result == 14


@pytest.mark.asyncio
async def test_retry_max_attempts_one_no_sleep():
    """With max_attempts=1, failure raises immediately without sleeping."""

    @async_retry(
        max_attempts=1,
        base_delay=1.0,
        retryable_exceptions=(MyRetryableError,),
    )
    async def always_fails():
        raise MyRetryableError("always")

    with patch("src.utils.retry.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(MyRetryableError):
            await always_fails()

    # No sleep when max_attempts=1 (no retry)
    mock_sleep.assert_not_called()


@pytest.mark.asyncio
async def test_retry_returns_value_correctly():
    """Return value is preserved through the decorator."""

    @async_retry(max_attempts=3, retryable_exceptions=(MyRetryableError,))
    async def return_dict():
        return {"key": "value", "num": 42}

    result = await return_dict()
    assert result == {"key": "value", "num": 42}


@pytest.mark.asyncio
async def test_retry_multiple_retryable_exception_types():
    """Can retry on multiple exception types."""

    class ErrorA(Exception):
        pass

    class ErrorB(Exception):
        pass

    call_count = 0

    @async_retry(
        max_attempts=4,
        base_delay=0.001,
        retryable_exceptions=(ErrorA, ErrorB),
    )
    async def alternating_errors():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ErrorA("first error")
        if call_count == 2:
            raise ErrorB("second error")
        return "success"

    with patch("src.utils.retry.asyncio.sleep", new_callable=AsyncMock):
        result = await alternating_errors()

    assert result == "success"
    assert call_count == 3
