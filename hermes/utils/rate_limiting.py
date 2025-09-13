"""Rate limiting utilities for HERMES."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict, Optional

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """In-memory rate limiter using sliding window algorithm."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # seconds
        self.requests: Dict[str, list] = {}

    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed based on rate limit."""
        current_time = time.time()

        # Get or create request history for identifier
        if identifier not in self.requests:
            self.requests[identifier] = []

        request_times = self.requests[identifier]

        # Remove old requests outside the window
        cutoff_time = current_time - self.window_size
        self.requests[identifier] = [t for t in request_times if t > cutoff_time]

        # Check if under rate limit
        if len(self.requests[identifier]) < self.requests_per_minute:
            self.requests[identifier].append(current_time)
            return True

        return False


class RedisRateLimiter:
    """Redis-based rate limiter for distributed rate limiting."""

    def __init__(self, redis_client, requests_per_minute: int = 60):
        self.redis = redis_client
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # seconds

    async def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed using Redis sliding window."""
        current_time = time.time()
        key = f"rate_limit:{identifier}"

        try:
            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()

            # Remove expired entries
            cutoff_time = current_time - self.window_size
            pipe.zremrangebyscore(key, 0, cutoff_time)

            # Count current requests in window
            pipe.zcard(key)

            # Add current request
            pipe.zadd(key, {str(current_time): current_time})

            # Set expiration
            pipe.expire(key, self.window_size)

            results = await pipe.execute()
            request_count = results[1]

            return request_count < self.requests_per_minute

        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            # Fail open - allow request if Redis is down
            return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests by tenant and user."""

    def __init__(
        self,
        app,
        rate_limiter: Optional[InMemoryRateLimiter | RedisRateLimiter] = None,
        tenant_requests_per_minute: int = 1000,
        user_requests_per_minute: int = 60,
        anonymous_requests_per_minute: int = 10,
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter or InMemoryRateLimiter()
        self.tenant_rpm = tenant_requests_per_minute
        self.user_rpm = user_requests_per_minute
        self.anonymous_rpm = anonymous_requests_per_minute

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and static assets
        if (
            request.url.path.startswith("/health")
            or request.url.path.startswith("/static")
            or request.url.path.startswith("/favicon")
        ):
            return await call_next(request)

        # Get identifiers
        client_ip = self._get_client_ip(request)
        tenant_id = getattr(request.state, "tenant_id", None)
        user_id = getattr(request.state, "user_id", None)

        # Rate limit by different scopes
        rate_limits_to_check = []

        if tenant_id:
            # Tenant-level rate limiting
            tenant_key = f"tenant:{tenant_id}"
            tenant_limiter = (
                RedisRateLimiter(self.rate_limiter.redis, self.tenant_rpm)
                if hasattr(self.rate_limiter, "redis")
                else InMemoryRateLimiter(self.tenant_rpm)
            )
            rate_limits_to_check.append((tenant_key, tenant_limiter))

        if user_id:
            # User-level rate limiting
            user_key = f"user:{user_id}"
            user_limiter = (
                RedisRateLimiter(self.rate_limiter.redis, self.user_rpm)
                if hasattr(self.rate_limiter, "redis")
                else InMemoryRateLimiter(self.user_rpm)
            )
            rate_limits_to_check.append((user_key, user_limiter))
        else:
            # Anonymous IP-based rate limiting
            ip_key = f"ip:{client_ip}"
            ip_limiter = (
                RedisRateLimiter(self.rate_limiter.redis, self.anonymous_rpm)
                if hasattr(self.rate_limiter, "redis")
                else InMemoryRateLimiter(self.anonymous_rpm)
            )
            rate_limits_to_check.append((ip_key, ip_limiter))

        # Check all applicable rate limits
        for identifier, limiter in rate_limits_to_check:
            allowed = (
                await limiter.is_allowed(identifier)
                if hasattr(limiter, "is_allowed")
                and asyncio.iscoroutinefunction(limiter.is_allowed)
                else limiter.is_allowed(identifier)
            )

            if not allowed:
                logger.warning(f"Rate limit exceeded for {identifier}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                    headers={"Retry-After": "60"},
                )

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, considering proxy headers."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"
