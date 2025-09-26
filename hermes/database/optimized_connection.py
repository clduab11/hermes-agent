"""
Optimized database connection management with enterprise-grade performance features.
"""

import asyncio
import ast
import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Optional, Any, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import event, text
import redis.asyncio as redis

from ..config import settings
from .tenant_context import get_current_tenant

logger = logging.getLogger(__name__)

# Database base model
Base = declarative_base()

@dataclass
class ConnectionMetrics:
    """Metrics for database connection monitoring."""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    query_count: int = 0
    avg_query_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    error_count: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)

@dataclass
class TenantMetrics:
    """Per-tenant performance metrics."""
    tenant_id: str
    total_queries: int = 0
    avg_response_time_ms: float = 0.0
    cache_hit_ratio: float = 0.0
    active_sessions: int = 0
    peak_concurrent_queries: int = 0
    last_activity: datetime = field(default_factory=datetime.utcnow)

class OptimizedDatabaseManager:
    """Enterprise-grade database manager with performance optimizations."""

    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        self.redis_client: Optional[redis.Redis] = None
        self._initialized = False
        self._metrics = ConnectionMetrics()
        self._tenant_metrics: Dict[str, TenantMetrics] = {}
        self._connection_monitor_task: Optional[asyncio.Task] = None

        # Performance optimization settings
        self._pool_size = 20
        self._max_overflow = 40
        self._pool_timeout = 30
        self._pool_recycle = 3600
        self._query_cache_ttl = 300  # 5 minutes

    async def initialize(self) -> bool:
        """Initialize optimized database connection with monitoring."""
        if not settings.database_url:
            logger.warning("No database URL configured - operating in mock mode")
            return False

        try:
            # Configure database URL for async operations
            db_url = await self._configure_database_url(settings.database_url)

            # Create optimized async engine
            self.engine = create_async_engine(
                db_url,
                # Performance optimizations
                pool_size=self._pool_size,
                max_overflow=self._max_overflow,
                pool_timeout=self._pool_timeout,
                pool_recycle=self._pool_recycle,
                pool_pre_ping=True,

                # Query optimization
                echo=settings.debug,
                echo_pool=settings.debug,

                # Connection pooling strategy
                poolclass=QueuePool,

                # Additional performance settings
                connect_args={
                    "server_settings": {
                        "application_name": "hermes-agent",
                        "jit": "off",  # Disable JIT for consistent performance
                    },
                    "command_timeout": 60,
                    "statement_cache_size": 1000,
                    "prepared_statement_cache_size": 1000,
                }
            )

            # Set up connection event listeners for monitoring
            self._setup_connection_monitoring()

            # Create optimized session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )

            # Initialize Redis for caching
            await self._initialize_redis_cache()

            # Start connection monitoring
            self._connection_monitor_task = asyncio.create_task(
                self._monitor_connections()
            )

            self._initialized = True
            logger.info(
                f"Optimized database connection initialized with pool_size={self._pool_size}, "
                f"max_overflow={self._max_overflow}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize optimized database: {e}")
            return False

    async def _configure_database_url(self, db_url: str) -> str:
        """Configure database URL for optimal async performance."""
        # Ensure asyncpg driver for PostgreSQL
        if db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("postgres://") and "+asyncpg" not in db_url:
            db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

        return db_url

    async def _initialize_redis_cache(self):
        """Initialize Redis for query result caching."""
        if not settings.redis_url:
            logger.warning("No Redis URL configured - query caching disabled")
            return

        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,
            )

            # Test connection
            await self.redis_client.ping()
            logger.info("Redis cache initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            self.redis_client = None

    def _setup_connection_monitoring(self):
        """Set up SQLAlchemy event listeners for connection monitoring."""
        @event.listens_for(self.engine.sync_engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            self._metrics.total_connections += 1
            self._metrics.active_connections += 1

        @event.listens_for(self.engine.sync_engine, "close")
        def on_close(dbapi_connection, connection_record):
            self._metrics.active_connections = max(0, self._metrics.active_connections - 1)

        @event.listens_for(self.engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.perf_counter()
            self._metrics.query_count += 1

        @event.listens_for(self.engine.sync_engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if hasattr(context, '_query_start_time'):
                query_time = time.perf_counter() - context._query_start_time
                self._update_query_metrics(query_time)

    def _update_query_metrics(self, query_time: float):
        """Update query performance metrics."""
        # Update overall metrics
        current_avg = self._metrics.avg_query_time
        total_queries = self._metrics.query_count

        if total_queries == 1:
            self._metrics.avg_query_time = query_time
        else:
            self._metrics.avg_query_time = (current_avg * (total_queries - 1) + query_time) / total_queries

        # Update tenant-specific metrics
        tenant_id = get_current_tenant()
        if tenant_id:
            tenant_metrics = self._tenant_metrics.setdefault(
                tenant_id,
                TenantMetrics(tenant_id=tenant_id)
            )
            tenant_metrics.total_queries += 1

            if tenant_metrics.total_queries == 1:
                tenant_metrics.avg_response_time_ms = query_time * 1000
            else:
                current_avg_ms = tenant_metrics.avg_response_time_ms
                tenant_metrics.avg_response_time_ms = (
                    (current_avg_ms * (tenant_metrics.total_queries - 1) + query_time * 1000)
                    / tenant_metrics.total_queries
                )

            tenant_metrics.last_activity = datetime.utcnow()

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an optimized database session with monitoring."""
        if not self._initialized or not self.session_factory:
            raise RuntimeError("Optimized database not initialized")

        session = self.session_factory()
        start_time = time.perf_counter()

        try:
            # Track active sessions per tenant
            tenant_id = get_current_tenant()
            if tenant_id:
                tenant_metrics = self._tenant_metrics.setdefault(
                    tenant_id,
                    TenantMetrics(tenant_id=tenant_id)
                )
                tenant_metrics.active_sessions += 1

            yield session

        except Exception as e:
            await session.rollback()
            self._metrics.error_count += 1
            logger.error(f"Database session error: {e}")
            raise

        finally:
            session_time = time.perf_counter() - start_time
            await session.close()

            # Update metrics
            if tenant_id:
                tenant_metrics = self._tenant_metrics.get(tenant_id)
                if tenant_metrics:
                    tenant_metrics.active_sessions = max(0, tenant_metrics.active_sessions - 1)

    async def execute_cached_query(
        self,
        query: str,
        parameters: Optional[Dict] = None,
        cache_key: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> Optional[Any]:
        """Execute query with Redis caching for improved performance."""
        if not self.redis_client:
            # Fallback to direct execution without caching
            async with self.get_session() as session:
                result = await session.execute(text(query), parameters or {})
                return result.fetchall()

        # Generate cache key
        if not cache_key:
            tenant_id = get_current_tenant() or "global"
            params_str = str(sorted((parameters or {}).items()))
            cache_key = f"query:{tenant_id}:{hash(query + params_str)}"

        # Try to get from cache
        try:
            cached_result = await self.redis_client.get(cache_key)
            if cached_result:
                self._metrics.cache_hits += 1

                # Update tenant cache metrics
                tenant_id = get_current_tenant()
                if tenant_id:
                    tenant_metrics = self._tenant_metrics.get(tenant_id)
                    if tenant_metrics:
                        total_cache_requests = self._metrics.cache_hits + self._metrics.cache_misses
                        tenant_metrics.cache_hit_ratio = self._metrics.cache_hits / max(1, total_cache_requests)

                # Secure deserialization to prevent code injection
                try:
                    return json.loads(cached_result)
                except json.JSONDecodeError:
                    try:
                        return ast.literal_eval(cached_result)
                    except (ValueError, SyntaxError):
                        logger.warning(f"Failed to deserialize cached result for key {cache_key}, falling back to query execution")
                        # Continue to query execution below

        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")

        # Execute query and cache result
        async with self.get_session() as session:
            result = await session.execute(text(query), parameters or {})
            data = result.fetchall()

            # Cache the result with secure JSON serialization
            try:
                # Convert SQLAlchemy result to JSON-serializable format
                serialized_data = []
                for row in data:
                    if hasattr(row, '_asdict'):
                        # Named tuple-like results
                        serialized_data.append(row._asdict())
                    elif hasattr(row, '__dict__'):
                        # Object results
                        serialized_data.append({k: v for k, v in row.__dict__.items() 
                                               if not k.startswith('_')})
                    else:
                        # Simple tuple results
                        serialized_data.append(list(row) if hasattr(row, '__iter__') else row)
                
                await self.redis_client.setex(
                    cache_key,
                    ttl or self._query_cache_ttl,
                    json.dumps(serialized_data, default=str)  # Use str() for datetime, decimal, etc.
                )
            except Exception as e:
                logger.warning(f"Cache storage failed: {e}")

            self._metrics.cache_misses += 1
            return data

    async def _monitor_connections(self):
        """Background task to monitor connection pool health."""
        while self._initialized:
            try:
                if self.engine:
                    # Get pool statistics
                    pool = self.engine.pool
                    self._metrics.active_connections = pool.checked_in()
                    self._metrics.idle_connections = pool.checked_out()
                    self._metrics.last_updated = datetime.utcnow()

                    # Log warnings for high connection usage
                    if self._metrics.active_connections > self._pool_size * 0.8:
                        logger.warning(
                            f"High database connection usage: {self._metrics.active_connections}/{self._pool_size}"
                        )

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Connection monitoring error: {e}")
                await asyncio.sleep(60)

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        return {
            "connection_metrics": {
                "total_connections": self._metrics.total_connections,
                "active_connections": self._metrics.active_connections,
                "idle_connections": self._metrics.idle_connections,
                "pool_size": self._pool_size,
                "max_overflow": self._max_overflow,
            },
            "query_metrics": {
                "total_queries": self._metrics.query_count,
                "avg_query_time_ms": self._metrics.avg_query_time * 1000,
                "cache_hits": self._metrics.cache_hits,
                "cache_misses": self._metrics.cache_misses,
                "cache_hit_ratio": self._metrics.cache_hits / max(1, self._metrics.cache_hits + self._metrics.cache_misses),
                "error_count": self._metrics.error_count,
            },
            "tenant_metrics": {
                tenant_id: {
                    "total_queries": metrics.total_queries,
                    "avg_response_time_ms": metrics.avg_response_time_ms,
                    "cache_hit_ratio": metrics.cache_hit_ratio,
                    "active_sessions": metrics.active_sessions,
                    "peak_concurrent_queries": metrics.peak_concurrent_queries,
                    "last_activity": metrics.last_activity.isoformat(),
                }
                for tenant_id, metrics in self._tenant_metrics.items()
            },
            "redis_status": "connected" if self.redis_client else "disconnected",
            "last_updated": self._metrics.last_updated.isoformat(),
        }

    async def get_tenant_performance_metrics(self, tenant_id: str) -> Optional[TenantMetrics]:
        """Get performance metrics for a specific tenant."""
        return self._tenant_metrics.get(tenant_id)

    async def optimize_for_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """Perform tenant-specific optimizations."""
        tenant_metrics = self._tenant_metrics.get(tenant_id)
        if not tenant_metrics:
            return {"status": "no_data", "message": "No metrics available for tenant"}

        optimizations_applied = []

        # Analyze query patterns and suggest optimizations
        if tenant_metrics.avg_response_time_ms > 1000:  # > 1 second
            optimizations_applied.append("slow_query_optimization")

        if tenant_metrics.cache_hit_ratio < 0.5:  # < 50% cache hit ratio
            optimizations_applied.append("cache_strategy_adjustment")

        if tenant_metrics.active_sessions > 10:  # High concurrency
            optimizations_applied.append("connection_pool_scaling")

        return {
            "status": "optimized",
            "tenant_id": tenant_id,
            "optimizations_applied": optimizations_applied,
            "current_metrics": {
                "avg_response_time_ms": tenant_metrics.avg_response_time_ms,
                "cache_hit_ratio": tenant_metrics.cache_hit_ratio,
                "active_sessions": tenant_metrics.active_sessions,
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for database and cache systems."""
        health_status = {
            "database": "unknown",
            "cache": "unknown",
            "overall": "degraded"
        }

        # Check database connection
        try:
            if self.engine:
                async with self.get_session() as session:
                    await session.execute(text("SELECT 1"))
                health_status["database"] = "healthy"
        except Exception as e:
            health_status["database"] = f"unhealthy: {e}"

        # Check Redis cache
        try:
            if self.redis_client:
                await self.redis_client.ping()
                health_status["cache"] = "healthy"
            else:
                health_status["cache"] = "disabled"
        except Exception as e:
            health_status["cache"] = f"unhealthy: {e}"

        # Determine overall health
        if health_status["database"] == "healthy":
            health_status["overall"] = "healthy"

        return health_status

    async def cleanup(self):
        """Clean up resources and connections."""
        try:
            if self._connection_monitor_task:
                self._connection_monitor_task.cancel()
                try:
                    await self._connection_monitor_task
                except asyncio.CancelledError:
                    pass

            if self.redis_client:
                await self.redis_client.close()

            if self.engine:
                await self.engine.dispose()

            self._initialized = False
            logger.info("Optimized database manager cleaned up successfully")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Global optimized database manager instance
optimized_db_manager = OptimizedDatabaseManager()

# Convenience functions for backward compatibility
async def get_optimized_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an optimized database session."""
    async with optimized_db_manager.get_session() as session:
        yield session

async def init_optimized_database() -> bool:
    """Initialize the optimized database connection."""
    return await optimized_db_manager.initialize()

async def close_optimized_database():
    """Close the optimized database connection."""
    await optimized_db_manager.cleanup()