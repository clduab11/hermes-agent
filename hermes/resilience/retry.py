"""
Retry logic with exponential backoff
September 2025 best practices
"""

import asyncio
import logging
import random
from functools import wraps
from typing import Any, Callable, Optional, Sequence, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryPolicy:
    """Configuration for retry behavior"""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retriable_exceptions: Optional[Sequence[Type[Exception]]] = None,
    ):
        """
        Initialize retry policy.
        
        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay between retries
            exponential_base: Base for exponential backoff calculation
            jitter: Add random jitter to prevent thundering herd
            retriable_exceptions: Exceptions that should trigger retry
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retriable_exceptions = retriable_exceptions or (Exception,)

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = self.initial_delay * (self.exponential_base ** attempt)
        
        # Cap at max_delay
        delay = min(delay, self.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.jitter:
            delay *= (0.5 + random.random())
        
        return delay

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if operation should be retried.
        
        Args:
            exception: Exception that occurred
            attempt: Current attempt number
            
        Returns:
            True if should retry
        """
        if attempt >= self.max_attempts:
            return False
        
        return isinstance(exception, self.retriable_exceptions)


def retry_async(
    policy: Optional[RetryPolicy] = None,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
) -> Callable:
    """
    Decorator for async functions with retry logic.
    
    Args:
        policy: RetryPolicy instance (overrides other parameters)
        max_attempts: Maximum retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @retry_async(max_attempts=5, initial_delay=2.0)
        async def fetch_data():
            return await api.get_data()
    """
    if policy is None:
        policy = RetryPolicy(
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            max_delay=max_delay,
        )

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for attempt in range(policy.max_attempts):
                try:
                    result = await func(*args, **kwargs)
                    
                    # Success - log retry stats if this wasn't first attempt
                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt + 1}/{policy.max_attempts}"
                        )
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    if not policy.should_retry(e, attempt):
                        # Don't retry this exception or out of attempts
                        logger.error(
                            f"{func.__name__} failed after {attempt + 1} attempts: {e}"
                        )
                        raise
                    
                    # Calculate delay and retry
                    delay = policy.calculate_delay(attempt)
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{policy.max_attempts}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    await asyncio.sleep(delay)
            
            # Exhausted all retries
            logger.error(
                f"{func.__name__} failed after {policy.max_attempts} attempts"
            )
            raise last_exception
        
        return wrapper
    return decorator


def exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
) -> float:
    """
    Calculate exponential backoff delay.
    
    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay
        exponential_base: Base for exponential calculation
        jitter: Add random jitter
        
    Returns:
        Delay in seconds
    """
    delay = base_delay * (exponential_base ** attempt)
    delay = min(delay, max_delay)
    
    if jitter:
        delay *= (0.5 + random.random())
    
    return delay
