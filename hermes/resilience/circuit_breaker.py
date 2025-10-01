"""
Circuit Breaker Pattern Implementation
September 2025 best practices for fault tolerance
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.
    
    Implements the Circuit Breaker pattern to prevent repeated calls
    to failing services, giving them time to recover.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service failing, requests blocked immediately
    - HALF_OPEN: Testing recovery, limited requests allowed
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
        timeout: float = 30.0,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Identifier for this circuit breaker
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            success_threshold: Successful calls needed in HALF_OPEN to close circuit
            timeout: Request timeout in seconds
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.timeout = timeout
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()

    async def call(
        self,
        func: Callable[..., Any],
        *args: Any,
        fallback: Optional[Callable[..., Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            fallback: Optional fallback function if circuit is open
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from func or fallback
            
        Raises:
            Exception: If circuit is open and no fallback provided
        """
        async with self._lock:
            # Check if we should attempt recovery
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_recovery():
                    logger.info(f"Circuit breaker [{self.name}]: Attempting recovery (HALF_OPEN)")
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.success_count = 0
                else:
                    # Circuit still open, use fallback if available
                    if fallback:
                        logger.warning(f"Circuit breaker [{self.name}]: OPEN, using fallback")
                        return await fallback(*args, **kwargs) if asyncio.iscoroutinefunction(fallback) else fallback(*args, **kwargs)
                    else:
                        raise Exception(f"Circuit breaker [{self.name}] is OPEN")
        
        # Attempt to execute the function
        try:
            # Add timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.timeout
            )
            
            # Success - handle state transition
            await self._on_success()
            return result
            
        except asyncio.TimeoutError as e:
            logger.error(f"Circuit breaker [{self.name}]: Timeout after {self.timeout}s")
            await self._on_failure()
            raise
        except Exception as e:
            logger.error(f"Circuit breaker [{self.name}]: Failure - {e}")
            await self._on_failure()
            
            # Try fallback
            if fallback:
                logger.info(f"Circuit breaker [{self.name}]: Using fallback after failure")
                return await fallback(*args, **kwargs) if asyncio.iscoroutinefunction(fallback) else fallback(*args, **kwargs)
            raise

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.recovery_timeout

    async def _on_success(self) -> None:
        """Handle successful call"""
        async with self._lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                logger.info(
                    f"Circuit breaker [{self.name}]: Success in HALF_OPEN "
                    f"({self.success_count}/{self.success_threshold})"
                )
                
                if self.success_count >= self.success_threshold:
                    # Recovered successfully
                    logger.info(f"Circuit breaker [{self.name}]: Recovered, closing circuit")
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
            elif self.state == CircuitBreakerState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

    async def _on_failure(self) -> None:
        """Handle failed call"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                # Failed during recovery attempt
                logger.warning(f"Circuit breaker [{self.name}]: Failed during recovery, reopening")
                self.state = CircuitBreakerState.OPEN
                self.success_count = 0
            elif self.state == CircuitBreakerState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    # Too many failures, open circuit
                    logger.error(
                        f"Circuit breaker [{self.name}]: Threshold reached "
                        f"({self.failure_count}/{self.failure_threshold}), opening circuit"
                    )
                    self.state = CircuitBreakerState.OPEN

    async def reset(self) -> None:
        """Manually reset the circuit breaker"""
        async with self._lock:
            logger.info(f"Circuit breaker [{self.name}]: Manual reset")
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None

    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
        }
