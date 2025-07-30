"""Retry utilities with exponential backoff."""

import asyncio
import random
from collections.abc import Callable
from typing import TypeVar

from ..logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


async def exponential_backoff_retry(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: tuple[type[Exception], ...] = (Exception,),
    retry_condition: Callable[[Exception], bool] | None = None,
) -> T:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: The async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Add random jitter to prevent thundering herd
        retry_on: Tuple of exception types to retry on
        retry_condition: Optional function to determine if exception should trigger retry
    
    Returns:
        The result of the function call
        
    Raises:
        The last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            # If it's a coroutine function, await it
            if asyncio.iscoroutinefunction(func):
                return await func()  # type: ignore[no-any-return]
            else:
                return func()
                
        except retry_on as e:
            last_exception = e
            
            # Check if we should retry based on the condition
            if retry_condition and not retry_condition(e):
                raise
            
            # Don't retry after the last attempt
            if attempt == max_retries:
                logger.warning(
                    f"Max retries ({max_retries}) exceeded for {func.__name__}"
                )
                raise
            
            # Calculate delay with exponential backoff
            delay = min(initial_delay * (exponential_base ** attempt), max_delay)
            
            # Add jitter if enabled
            if jitter:
                delay = delay * (0.5 + random.random())  # noqa: S311
            
            logger.info(
                f"Retry attempt {attempt + 1}/{max_retries} for {func.__name__} "
                f"after {delay:.2f}s delay. Error: {str(e)}"
            )
            
            await asyncio.sleep(delay)
    
    # This should never be reached, but just in case
    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected retry loop exit")


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        timeout_retries: int = 2,
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.timeout_retries = timeout_retries
    
    def should_retry_timeout(self, error: Exception) -> bool:
        """Check if a timeout error should be retried."""
        error_msg = str(error).lower()
        return "timeout" in error_msg or "timed out" in error_msg
    
    def should_retry_network(self, error: Exception) -> bool:
        """Check if a network error should be retried."""
        error_msg = str(error).lower()
        network_errors = [
            "network", "connection", "refused", "reset", 
            "unreachable", "dns", "resolve", "socket"
        ]
        return any(err in error_msg for err in network_errors)