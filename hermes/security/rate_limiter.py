"""Enhanced rate limiting with Redis backend for production."""

import asyncio
import time
from typing import Dict, Optional

import redis.asyncio as aioredis
import structlog
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


class ProductionRateLimiter:
    """Production-grade rate limiter with Redis backend."""

    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
        self.limits = {
            "default": {"requests": 100, "window": 60},  # 100 requests per minute
            "auth": {"requests": 10, "window": 60},      # 10 auth attempts per minute
            "voice": {"requests": 30, "window": 60},     # 30 voice requests per minute
            "api": {"requests": 200, "window": 60},      # 200 API calls per minute
        }

    async def is_allowed(self, key: str, limit_type: str = "default") -> bool:
        """Check if request is within rate limits."""
        try:
            limit_config = self.limits.get(limit_type, self.limits["default"])
            window = limit_config["window"]
            max_requests = limit_config["requests"]

            now = int(time.time())
            window_start = now - window

            # Use Redis sliding window
            pipe = self.redis.pipeline()

            # Remove expired entries
            await pipe.zremrangebyscore(key, 0, window_start)

            # Count current requests
            current_count = await pipe.zcard(key)

            if current_count >= max_requests:
                logger.warning(f"Rate limit exceeded for key: {key}, type: {limit_type}")
                return False

            # Add current request
            await pipe.zadd(key, {str(now): now})
            await pipe.expire(key, window)
            await pipe.execute()

            return True

        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open for availability
            return True

    async def get_remaining(self, key: str, limit_type: str = "default") -> int:
        """Get remaining requests in current window."""
        try:
            limit_config = self.limits.get(limit_type, self.limits["default"])
            window = limit_config["window"]
            max_requests = limit_config["requests"]

            now = int(time.time())
            window_start = now - window

            await self.redis.zremrangebyscore(key, 0, window_start)
            current_count = await self.redis.zcard(key)

            return max(0, max_requests - current_count)

        except Exception as e:
            logger.error(f"Error getting remaining requests: {e}")
            return 100  # Default fallback


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    def __init__(self, app, redis_url: str):
        super().__init__(app)
        self.rate_limiter = ProductionRateLimiter(redis_url)

    def get_client_ip(self, request: Request) -> str:
        """Get client IP with proxy support."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host

    def get_limit_type(self, path: str) -> str:
        """Determine rate limit type based on path."""
        if path.startswith("/auth"):
            return "auth"
        elif path.startswith("/voice") or path.startswith("/ws"):
            return "voice"
        elif path.startswith("/api"):
            return "api"
        return "default"

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to requests."""
        client_ip = self.get_client_ip(request)
        path = request.url.path
        limit_type = self.get_limit_type(path)

        # Create rate limit key
        key = f"rate_limit:{limit_type}:{client_ip}"

        # Check rate limit
        allowed = await self.rate_limiter.is_allowed(key, limit_type)

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "retry_after": 60,
                    "limit_type": limit_type
                }
            )

        # Add rate limit headers
        response = await call_next(request)
        remaining = await self.rate_limiter.get_remaining(key, limit_type)

        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.limits[limit_type]["requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)

        return response