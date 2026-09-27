from __future__ import annotations

import asyncio
import logging

import httpx
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("ragbench.retry")

DEFAULT_RETRYABLE_STATUS_CODES = (429, 500, 502, 503, 504)


class RetryPolicy(BaseModel):
    """Configurable and bounded retry policy for external network operations.

    Distinguishes retryable failures (rate limits, transient 5xx, network timeouts)
    from non-retryable failures (4xx client validation errors, malformed responses).
    """

    model_config = ConfigDict(frozen=True)

    max_attempts: int = Field(default=3, ge=1, le=10)
    initial_backoff_seconds: float = Field(default=0.1, ge=0.0)
    max_backoff_seconds: float = Field(default=2.0, ge=0.0)
    backoff_factor: float = Field(default=2.0, ge=1.0)
    retryable_status_codes: tuple[int, ...] = DEFAULT_RETRYABLE_STATUS_CODES
    retry_on_timeout: bool = True

    def is_retryable(self, exc: Exception) -> bool:
        """Determines whether an exception is safe and transient to retry."""
        if isinstance(exc, httpx.TimeoutException):
            return self.retry_on_timeout
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code in self.retryable_status_codes
        if isinstance(exc, httpx.RequestError):
            return True
        # Do not retry deterministic format or validation errors
        return False

    def compute_backoff(self, attempt: int) -> float:
        """Computes exponential backoff bounded by max_backoff_seconds."""
        if attempt <= 1:
            return self.initial_backoff_seconds
        delay = self.initial_backoff_seconds * (self.backoff_factor ** (attempt - 1))
        return min(delay, self.max_backoff_seconds)


async def execute_with_retry(
    coroutine_func,
    policy: RetryPolicy,
    *,
    operation_name: str = "network_request",
):
    """Executes a coroutine function with bounded retries according to policy."""
    last_exc: Exception | None = None
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return await coroutine_func()
        except Exception as exc:
            last_exc = exc
            is_retryable = policy.is_retryable(exc)
            if not is_retryable or attempt >= policy.max_attempts:
                logger.warning(
                    "retry_exhausted_or_not_retryable",
                    extra={
                        "event": "retry_failure",
                        "operation": operation_name,
                        "attempt": attempt,
                        "max_attempts": policy.max_attempts,
                        "is_retryable": is_retryable,
                        "error_type": type(exc).__name__,
                    },
                )
                raise
            delay = policy.compute_backoff(attempt)
            logger.info(
                "retry_backoff",
                extra={
                    "event": "retry_attempt",
                    "operation": operation_name,
                    "attempt": attempt,
                    "delay_seconds": delay,
                    "error_type": type(exc).__name__,
                },
            )
            await asyncio.sleep(delay)

    assert last_exc is not None
    raise last_exc
