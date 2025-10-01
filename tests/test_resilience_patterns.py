"""
Test resilience patterns (circuit breaker, retry)
"""

import os
os.environ["OPENAI_API_KEY"] = "test-key-123"
os.environ["DEBUG"] = "true"

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock

from hermes.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerState
from hermes.resilience.retry import RetryPolicy, retry_async, exponential_backoff


class TestCircuitBreaker:
    """Test circuit breaker pattern"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_initialization(self):
        """Test circuit breaker can be initialized"""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=3,
            recovery_timeout=5.0
        )
        
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_successful_call(self):
        """Test successful function call"""
        cb = CircuitBreaker(name="test")
        
        async def success_func():
            return "success"
        
        result = await cb.call(success_func)
        
        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_opens_on_failures(self):
        """Test circuit opens after threshold failures"""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=3
        )
        
        async def failing_func():
            raise Exception("Test failure")
        
        # Execute failures to open circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await cb.call(failing_func)
        
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.failure_count == 3

    @pytest.mark.asyncio
    async def test_fallback_function(self):
        """Test fallback function when circuit is open"""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=1
        )
        
        async def failing_func():
            raise Exception("Test failure")
        
        async def fallback_func():
            return "fallback result"
        
        # Trigger failure to open circuit
        result = await cb.call(failing_func, fallback=fallback_func)
        assert result == "fallback result"
        
        # Circuit should be open
        result = await cb.call(failing_func, fallback=fallback_func)
        assert result == "fallback result"

    @pytest.mark.asyncio
    async def test_circuit_recovery(self):
        """Test circuit recovery from OPEN to CLOSED"""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=1,
            recovery_timeout=0.1,  # Short timeout for testing
            success_threshold=2
        )
        
        async def failing_func():
            raise Exception("Test failure")
        
        async def success_func():
            return "success"
        
        # Open the circuit
        with pytest.raises(Exception):
            await cb.call(failing_func)
        
        assert cb.state == CircuitBreakerState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(0.2)
        
        # Should attempt recovery (HALF_OPEN)
        await cb.call(success_func)
        assert cb.state == CircuitBreakerState.HALF_OPEN
        
        # Second success should close circuit
        await cb.call(success_func)
        assert cb.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting circuit breaker statistics"""
        cb = CircuitBreaker(name="test")
        
        stats = cb.get_stats()
        
        assert stats["name"] == "test"
        assert stats["state"] == "closed"
        assert stats["failure_count"] == 0


class TestRetryLogic:
    """Test retry logic with exponential backoff"""

    def test_retry_policy_initialization(self):
        """Test retry policy can be initialized"""
        policy = RetryPolicy(
            max_attempts=5,
            initial_delay=1.0,
            exponential_base=2.0
        )
        
        assert policy.max_attempts == 5
        assert policy.initial_delay == 1.0

    def test_calculate_delay(self):
        """Test delay calculation"""
        policy = RetryPolicy(
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=False
        )
        
        assert policy.calculate_delay(0) == 1.0
        assert policy.calculate_delay(1) == 2.0
        assert policy.calculate_delay(2) == 4.0

    def test_should_retry(self):
        """Test retry decision logic"""
        policy = RetryPolicy(max_attempts=3)
        
        assert policy.should_retry(Exception("test"), 0) is True
        assert policy.should_retry(Exception("test"), 2) is True
        assert policy.should_retry(Exception("test"), 3) is False

    @pytest.mark.asyncio
    async def test_retry_decorator_success(self):
        """Test retry decorator with successful call"""
        call_count = 0
        
        @retry_async(max_attempts=3)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await test_func()
        
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_decorator_eventual_success(self):
        """Test retry decorator with eventual success"""
        call_count = 0
        
        @retry_async(max_attempts=3, initial_delay=0.1)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = await test_func()
        
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_decorator_all_failures(self):
        """Test retry decorator exhausts all attempts"""
        call_count = 0
        
        @retry_async(max_attempts=3, initial_delay=0.1)
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent failure")
        
        with pytest.raises(Exception):
            await test_func()
        
        assert call_count == 3

    def test_exponential_backoff(self):
        """Test exponential backoff calculation"""
        delay = exponential_backoff(0, base_delay=1.0, jitter=False)
        assert delay == 1.0
        
        delay = exponential_backoff(2, base_delay=1.0, jitter=False)
        assert delay == 4.0
        
        # Test with jitter
        delay = exponential_backoff(1, base_delay=1.0, jitter=True)
        assert 1.0 <= delay <= 4.0  # Should be between base and max
