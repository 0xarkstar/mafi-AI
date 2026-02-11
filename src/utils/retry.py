"""Async retry decorator with exponential backoff and jitter."""

import asyncio
import functools
import random
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

import openai

from src.utils.logger import get_logger

T = TypeVar("T")

log = get_logger(__name__)


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    multiplier: float = 2.0,
    retryable_exceptions: tuple[type[Exception], ...] = (
        openai.APIError,
        openai.RateLimitError,
        openai.APIConnectionError,
        openai.InternalServerError,
    ),
) -> Callable[
    [Callable[..., Coroutine[Any, Any, T]]],
    Callable[..., Coroutine[Any, Any, T]],
]:
    """Decorator for async functions with exponential backoff retry.

    Args:
        max_attempts: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay between retries.
        multiplier: Delay multiplier per attempt.
        retryable_exceptions: Tuple of exception types to retry on.
    """

    def decorator(
        func: Callable[..., Coroutine[Any, Any, T]],
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as exc:
                    last_exception = exc

                    if attempt == max_attempts:
                        break

                    delay = _calculate_delay(attempt, base_delay, max_delay, multiplier)

                    log.warning(
                        "retrying",
                        function=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        delay=delay,
                        error=str(exc),
                    )

                    await asyncio.sleep(delay)

            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator


def _calculate_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
    multiplier: float,
) -> float:
    """Calculate retry delay with exponential backoff and jitter."""
    # Exponential backoff with jitter
    delay = base_delay * (multiplier ** (attempt - 1))
    jitter = random.uniform(0, delay * 0.1)  # noqa: S311
    return min(delay + jitter, max_delay)
