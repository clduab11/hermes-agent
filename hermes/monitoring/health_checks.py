"""
Enterprise-grade health checks for HERMES production deployment.

Provides deep dependency validation for law firm customers requiring
bulletproof reliability and detailed system status.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:
    httpx = None

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy import text
except ImportError:
    AsyncSession = None
    create_async_engine = None
    text = None

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a single health check."""
    component: str
    status: HealthStatus
    latency_ms: float = 0.0
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "component": self.component,
            "status": self.status.value,
            "latency_ms": round(self.latency_ms, 2),
            "message": self.message,
            "details": self.details or {},
            "timestamp": self.timestamp.isoformat(),
        }


class HealthChecker:
    """
    Comprehensive health checker for HERMES infrastructure.

    Validates:
    - Database connectivity and responsiveness
    - Redis cache connectivity
    - External API availability (OpenAI, Clio)
    - Disk space and memory
    - Service dependencies
    """

    # Health check timeouts
    DB_TIMEOUT_MS = 1000  # 1 second
    REDIS_TIMEOUT_MS = 500  # 500ms
    API_TIMEOUT_MS = 3000  # 3 seconds

    # Critical thresholds
    DISK_SPACE_WARNING_PCT = 20.0  # Warn if <20% free
    MEMORY_WARNING_PCT = 10.0  # Warn if <10% free

    def __init__(
        self,
        database_url: Optional[str] = None,
        redis_url: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        clio_api_base: Optional[str] = None,
    ):
        """
        Initialize health checker.

        Args:
            database_url: PostgreSQL connection string
            redis_url: Redis connection string
            openai_api_key: OpenAI API key
            clio_api_base: Clio API base URL
        """
        self.database_url = database_url
        self.redis_url = redis_url
        self.openai_api_key = openai_api_key
        self.clio_api_base = clio_api_base

        self._redis_client: Optional[redis.Redis] = None
        self._db_engine = None

    async def check_all(self) -> Dict[str, Any]:
        """
        Run all health checks and return comprehensive status.

        Returns:
            dict with overall health and individual component statuses
        """
        start_time = datetime.utcnow()
        results: List[HealthCheckResult] = []

        # Run all checks concurrently
        checks = [
            self.check_database(),
            self.check_redis(),
            self.check_openai_api(),
            self.check_disk_space(),
            self.check_memory(),
        ]

        # Only check Clio if configured
        if self.clio_api_base:
            checks.append(self.check_clio_api())

        check_results = await asyncio.gather(*checks, return_exceptions=True)

        # Process results
        for result in check_results:
            if isinstance(result, Exception):
                results.append(HealthCheckResult(
                    component="unknown",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(result)}"
                ))
            else:
                results.append(result)

        # Determine overall status
        overall_status = self._calculate_overall_status(results)

        total_latency = (datetime.utcnow() - start_time).total_seconds() * 1000

        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "latency_ms": round(total_latency, 2),
            "components": [r.to_dict() for r in results],
            "summary": self._generate_summary(results),
        }

    async def check_basic(self) -> Dict[str, Any]:
        """
        Quick health check for load balancer (minimal latency).

        Returns:
            Simple health status
        """
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def check_database(self) -> HealthCheckResult:
        """Check database connectivity and responsiveness."""
        if not self.database_url:
            return HealthCheckResult(
                component="database",
                status=HealthStatus.UNKNOWN,
                message="Database not configured"
            )

        start_time = asyncio.get_event_loop().time()

        try:
            # Create engine if not exists
            if not self._db_engine:
                self._db_engine = create_async_engine(
                    self.database_url,
                    pool_pre_ping=True,
                    pool_size=1,
                    max_overflow=0,
                )

            # Test query with timeout
            async with asyncio.timeout(self.DB_TIMEOUT_MS / 1000):
                async with self._db_engine.connect() as conn:
                    result = await conn.execute(text("SELECT 1"))
                    await result.fetchone()

            latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000

            # Check if latency acceptable
            if latency_ms > self.DB_TIMEOUT_MS:
                status = HealthStatus.DEGRADED
                message = f"Database slow ({latency_ms:.0f}ms > {self.DB_TIMEOUT_MS}ms)"
            else:
                status = HealthStatus.HEALTHY
                message = "Database responsive"

            return HealthCheckResult(
                component="database",
                status=status,
                latency_ms=latency_ms,
                message=message,
                details={"connection_pool": "active"}
            )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                component="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database timeout (>{self.DB_TIMEOUT_MS}ms)"
            )
        except Exception as e:
            return HealthCheckResult(
                component="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database error: {str(e)}"
            )

    async def check_redis(self) -> HealthCheckResult:
        """Check Redis cache connectivity."""
        if not self.redis_url:
            return HealthCheckResult(
                component="redis",
                status=HealthStatus.UNKNOWN,
                message="Redis not configured"
            )

        start_time = asyncio.get_event_loop().time()

        try:
            # Create client if not exists
            if not self._redis_client:
                self._redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=self.REDIS_TIMEOUT_MS / 1000,
                    socket_timeout=self.REDIS_TIMEOUT_MS / 1000,
                )

            # Test ping with timeout
            async with asyncio.timeout(self.REDIS_TIMEOUT_MS / 1000):
                await self._redis_client.ping()

            latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000

            # Check if latency acceptable
            if latency_ms > self.REDIS_TIMEOUT_MS:
                status = HealthStatus.DEGRADED
                message = f"Redis slow ({latency_ms:.0f}ms > {self.REDIS_TIMEOUT_MS}ms)"
            else:
                status = HealthStatus.HEALTHY
                message = "Redis responsive"

            # Get cache info
            info = await self._redis_client.info("stats")

            return HealthCheckResult(
                component="redis",
                status=status,
                latency_ms=latency_ms,
                message=message,
                details={
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                }
            )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                component="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis timeout (>{self.REDIS_TIMEOUT_MS}ms)"
            )
        except Exception as e:
            return HealthCheckResult(
                component="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis error: {str(e)}"
            )

    async def check_openai_api(self) -> HealthCheckResult:
        """Check OpenAI API availability."""
        if not self.openai_api_key or not httpx:
            return HealthCheckResult(
                component="openai_api",
                status=HealthStatus.UNKNOWN,
                message="OpenAI API not configured or httpx not installed"
            )

        start_time = asyncio.get_event_loop().time()

        try:
            async with httpx.AsyncClient() as client:
                # Test models endpoint (lightweight)
                async with asyncio.timeout(self.API_TIMEOUT_MS / 1000):
                    response = await client.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {self.openai_api_key}"}
                    )

            latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000

            if response.status_code == 200:
                status = HealthStatus.HEALTHY
                message = "OpenAI API accessible"
            elif response.status_code == 429:
                status = HealthStatus.DEGRADED
                message = "OpenAI API rate limited"
            else:
                status = HealthStatus.DEGRADED
                message = f"OpenAI API returned {response.status_code}"

            return HealthCheckResult(
                component="openai_api",
                status=status,
                latency_ms=latency_ms,
                message=message,
                details={"status_code": response.status_code}
            )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                component="openai_api",
                status=HealthStatus.UNHEALTHY,
                message=f"OpenAI API timeout (>{self.API_TIMEOUT_MS}ms)"
            )
        except Exception as e:
            return HealthCheckResult(
                component="openai_api",
                status=HealthStatus.UNHEALTHY,
                message=f"OpenAI API error: {str(e)}"
            )

    async def check_clio_api(self) -> HealthCheckResult:
        """Check Clio API availability."""
        if not self.clio_api_base or not httpx:
            return HealthCheckResult(
                component="clio_api",
                status=HealthStatus.UNKNOWN,
                message="Clio API not configured"
            )

        start_time = asyncio.get_event_loop().time()

        try:
            async with httpx.AsyncClient() as client:
                # Check API base URL
                async with asyncio.timeout(self.API_TIMEOUT_MS / 1000):
                    response = await client.get(f"{self.clio_api_base}/health")

            latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000

            if response.status_code in (200, 401):  # 401 is ok, means API is up
                status = HealthStatus.HEALTHY
                message = "Clio API accessible"
            else:
                status = HealthStatus.DEGRADED
                message = f"Clio API returned {response.status_code}"

            return HealthCheckResult(
                component="clio_api",
                status=status,
                latency_ms=latency_ms,
                message=message
            )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                component="clio_api",
                status=HealthStatus.UNHEALTHY,
                message=f"Clio API timeout (>{self.API_TIMEOUT_MS}ms)"
            )
        except Exception as e:
            return HealthCheckResult(
                component="clio_api",
                status=HealthStatus.DEGRADED,
                message=f"Clio API check failed: {str(e)}"
            )

    async def check_disk_space(self) -> HealthCheckResult:
        """Check available disk space."""
        try:
            import shutil

            total, used, free = shutil.disk_usage("/")

            free_percent = (free / total) * 100

            if free_percent < self.DISK_SPACE_WARNING_PCT:
                status = HealthStatus.DEGRADED
                message = f"Low disk space ({free_percent:.1f}% free)"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk space adequate ({free_percent:.1f}% free)"

            return HealthCheckResult(
                component="disk_space",
                status=status,
                message=message,
                details={
                    "total_gb": round(total / (1024**3), 2),
                    "used_gb": round(used / (1024**3), 2),
                    "free_gb": round(free / (1024**3), 2),
                    "free_percent": round(free_percent, 1),
                }
            )

        except Exception as e:
            return HealthCheckResult(
                component="disk_space",
                status=HealthStatus.UNKNOWN,
                message=f"Could not check disk space: {str(e)}"
            )

    async def check_memory(self) -> HealthCheckResult:
        """Check available system memory."""
        try:
            import psutil

            memory = psutil.virtual_memory()
            available_percent = memory.available / memory.total * 100

            if available_percent < self.MEMORY_WARNING_PCT:
                status = HealthStatus.DEGRADED
                message = f"Low memory ({available_percent:.1f}% available)"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory adequate ({available_percent:.1f}% available)"

            return HealthCheckResult(
                component="memory",
                status=status,
                message=message,
                details={
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": round(memory.percent, 1),
                }
            )

        except ImportError:
            return HealthCheckResult(
                component="memory",
                status=HealthStatus.UNKNOWN,
                message="psutil not installed, cannot check memory"
            )
        except Exception as e:
            return HealthCheckResult(
                component="memory",
                status=HealthStatus.UNKNOWN,
                message=f"Could not check memory: {str(e)}"
            )

    def _calculate_overall_status(self, results: List[HealthCheckResult]) -> HealthStatus:
        """Calculate overall system health from component health."""
        if not results:
            return HealthStatus.UNKNOWN

        # Any unhealthy component = overall unhealthy
        if any(r.status == HealthStatus.UNHEALTHY for r in results):
            return HealthStatus.UNHEALTHY

        # Any degraded component = overall degraded
        if any(r.status == HealthStatus.DEGRADED for r in results):
            return HealthStatus.DEGRADED

        # All healthy = overall healthy
        if all(r.status == HealthStatus.HEALTHY for r in results):
            return HealthStatus.HEALTHY

        return HealthStatus.UNKNOWN

    def _generate_summary(self, results: List[HealthCheckResult]) -> Dict[str, Any]:
        """Generate summary statistics from health check results."""
        total = len(results)
        healthy = sum(1 for r in results if r.status == HealthStatus.HEALTHY)
        degraded = sum(1 for r in results if r.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for r in results if r.status == HealthStatus.UNHEALTHY)
        unknown = sum(1 for r in results if r.status == HealthStatus.UNKNOWN)

        return {
            "total_components": total,
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "unknown": unknown,
            "health_percentage": round((healthy / total * 100) if total > 0 else 0, 1),
        }

    async def cleanup(self) -> None:
        """Clean up health checker resources."""
        if self._redis_client:
            await self._redis_client.close()
        if self._db_engine:
            await self._db_engine.dispose()
