"""
Advanced tenant-aware caching manager with Redis clustering and performance optimization.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

import redis.asyncio as redis
from redis.asyncio.cluster import RedisCluster
from redis.backoff import ExponentialBackoff
from redis.retry import Retry

from ..config import settings
from ..database.tenant_context import get_current_tenant

logger = logging.getLogger(__name__)

class CacheLevel(Enum):
    """Cache level priorities."""
    L1_MEMORY = "memory"      # In-memory cache (fastest)
    L2_REDIS = "redis"        # Redis cache (fast, persistent)
    L3_PERSISTENT = "persistent"  # Database or file cache (slowest)

@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    memory_usage_bytes: int = 0
    avg_lookup_time_ms: float = 0.0
    tenant_distribution: Dict[str, int] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    @property
    def hit_ratio(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

@dataclass
class CacheItem:
    """Cached item with metadata."""
    key: str
    value: Any
    tenant_id: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    size_bytes: int = 0

class TenantCacheManager:
    """Enterprise-grade tenant-aware cache manager with multi-level caching."""

    def __init__(self, redis_url: Optional[str] = None, max_memory_items: int = 10000):
        self.redis_url = redis_url or settings.redis_url
        self.redis_client: Optional[Union[redis.Redis, RedisCluster]] = None
        self.redis_cluster = False

        # Multi-level cache
        self._memory_cache: Dict[str, CacheItem] = {}
        self._max_memory_items = max_memory_items

        # Performance metrics
        self._metrics = CacheMetrics()

        # Cache configuration
        self._default_ttl = 3600  # 1 hour
        self._tenant_ttl_overrides: Dict[str, int] = {}

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None

        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize the cache manager with Redis and clustering support."""
        if not self.redis_url:
            logger.warning("No Redis URL configured - using memory cache only")
            return True

        try:
            # Detect if we should use Redis Cluster
            if "cluster" in self.redis_url.lower() or "," in self.redis_url:
                await self._initialize_cluster()
            else:
                await self._initialize_single_redis()

            # Start background tasks
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_items())
            self._metrics_task = asyncio.create_task(self._update_metrics_periodically())

            self._initialized = True
            logger.info("Tenant cache manager initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize cache manager: {e}")
            return False

    async def _initialize_single_redis(self):
        """Initialize single Redis instance."""
        self.redis_client = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30,
            retry=Retry(ExponentialBackoff(), 3),
            retry_on_timeout=True,
            retry_on_error=[ConnectionError, TimeoutError]
        )

        # Test connection
        await self.redis_client.ping()
        logger.info("Single Redis instance connected")

    async def _initialize_cluster(self):
        """Initialize Redis Cluster."""
        # Parse cluster nodes from URL
        nodes = self.redis_url.replace("redis://", "").replace("rediss://", "").split(",")
        startup_nodes = [{"host": node.split(":")[0], "port": int(node.split(":")[1])} for node in nodes]

        self.redis_client = RedisCluster(
            startup_nodes=startup_nodes,
            decode_responses=True,
            skip_full_coverage_check=True,
            max_connections=20,
            retry=Retry(ExponentialBackoff(), 3)
        )
        self.redis_cluster = True

        # Test cluster connection
        await self.redis_client.ping()
        logger.info("Redis Cluster connected")

    def _get_cache_key(self, key: str, tenant_id: Optional[str] = None) -> str:
        """Generate tenant-aware cache key."""
        if not tenant_id:
            tenant_id = get_current_tenant() or "global"

        return f"hermes:cache:{tenant_id}:{key}"

    def _serialize_value(self, value: Any) -> str:
        """Serialize value for cache storage."""
        if isinstance(value, (str, int, float, bool)):
            return json.dumps({"type": "primitive", "value": value})
        else:
            return json.dumps({"type": "complex", "value": value}, default=str)

    def _deserialize_value(self, serialized: str) -> Any:
        """Deserialize value from cache storage."""
        try:
            data = json.loads(serialized)
            return data["value"]
        except (json.JSONDecodeError, KeyError):
            return serialized

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tenant_id: Optional[str] = None,
        cache_level: CacheLevel = CacheLevel.L2_REDIS
    ) -> bool:
        """Set a cached value with multi-level support."""
        start_time = time.perf_counter()

        try:
            tenant_id = tenant_id or get_current_tenant() or "global"
            cache_key = self._get_cache_key(key, tenant_id)
            ttl = ttl or self._tenant_ttl_overrides.get(tenant_id, self._default_ttl)

            serialized_value = self._serialize_value(value)
            size_bytes = len(serialized_value.encode('utf-8'))

            # Create cache item
            cache_item = CacheItem(
                key=cache_key,
                value=value,
                tenant_id=tenant_id,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(seconds=ttl),
                size_bytes=size_bytes
            )

            success = True

            # L1: Memory cache
            if cache_level in [CacheLevel.L1_MEMORY]:
                await self._set_memory_cache(cache_item)

            # L2: Redis cache
            if cache_level in [CacheLevel.L2_REDIS] and self.redis_client:
                try:
                    await self.redis_client.setex(cache_key, ttl, serialized_value)

                    # Also cache in memory for faster access
                    if len(self._memory_cache) < self._max_memory_items:
                        await self._set_memory_cache(cache_item)

                except Exception as e:
                    logger.error(f"Redis cache set failed: {e}")
                    success = False

            # Update metrics
            self._update_set_metrics(tenant_id, size_bytes, time.perf_counter() - start_time)

            return success

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def _set_memory_cache(self, cache_item: CacheItem):
        """Set item in memory cache with LRU eviction."""
        # Implement LRU eviction if at capacity
        if len(self._memory_cache) >= self._max_memory_items:
            await self._evict_lru_items(count=max(1, self._max_memory_items // 10))

        self._memory_cache[cache_item.key] = cache_item

    async def get(
        self,
        key: str,
        tenant_id: Optional[str] = None,
        cache_level: CacheLevel = CacheLevel.L2_REDIS
    ) -> Optional[Any]:
        """Get cached value with multi-level lookup."""
        start_time = time.perf_counter()

        try:
            tenant_id = tenant_id or get_current_tenant() or "global"
            cache_key = self._get_cache_key(key, tenant_id)

            # L1: Memory cache lookup
            memory_item = self._memory_cache.get(cache_key)
            if memory_item:
                if not self._is_expired(memory_item):
                    memory_item.last_accessed = datetime.utcnow()
                    memory_item.access_count += 1
                    self._metrics.hits += 1
                    self._update_lookup_metrics(time.perf_counter() - start_time)
                    return memory_item.value
                else:
                    # Remove expired item
                    del self._memory_cache[cache_key]

            # L2: Redis cache lookup
            if cache_level in [CacheLevel.L2_REDIS] and self.redis_client:
                try:
                    serialized_value = await self.redis_client.get(cache_key)
                    if serialized_value:
                        value = self._deserialize_value(serialized_value)

                        # Cache in memory for faster future access
                        if len(self._memory_cache) < self._max_memory_items:
                            cache_item = CacheItem(
                                key=cache_key,
                                value=value,
                                tenant_id=tenant_id,
                                created_at=datetime.utcnow(),
                                size_bytes=len(serialized_value.encode('utf-8'))
                            )
                            self._memory_cache[cache_key] = cache_item

                        self._metrics.hits += 1
                        self._update_lookup_metrics(time.perf_counter() - start_time)
                        return value

                except Exception as e:
                    logger.error(f"Redis cache get failed: {e}")

            # Cache miss
            self._metrics.misses += 1
            self._update_lookup_metrics(time.perf_counter() - start_time)
            return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self._metrics.misses += 1
            return None

    async def delete(self, key: str, tenant_id: Optional[str] = None) -> bool:
        """Delete cached value from all levels."""
        try:
            tenant_id = tenant_id or get_current_tenant() or "global"
            cache_key = self._get_cache_key(key, tenant_id)

            success = True

            # Remove from memory cache
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]

            # Remove from Redis cache
            if self.redis_client:
                try:
                    await self.redis_client.delete(cache_key)
                except Exception as e:
                    logger.error(f"Redis cache delete failed: {e}")
                    success = False

            return success

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def invalidate_tenant(self, tenant_id: str) -> int:
        """Invalidate all cache entries for a specific tenant."""
        try:
            pattern = f"hermes:cache:{tenant_id}:*"
            invalidated_count = 0

            # Invalidate memory cache
            keys_to_remove = [key for key in self._memory_cache.keys() if tenant_id in key]
            for key in keys_to_remove:
                del self._memory_cache[key]
                invalidated_count += 1

            # Invalidate Redis cache
            if self.redis_client:
                try:
                    if self.redis_cluster:
                        # For cluster, we need to scan each node
                        keys = []
                        for node in self.redis_client.get_nodes():
                            node_keys = await node.keys(pattern)
                            keys.extend(node_keys)
                    else:
                        keys = await self.redis_client.keys(pattern)

                    if keys:
                        await self.redis_client.delete(*keys)
                        invalidated_count += len(keys)

                except Exception as e:
                    logger.error(f"Redis tenant invalidation failed: {e}")

            logger.info(f"Invalidated {invalidated_count} cache entries for tenant {tenant_id}")
            return invalidated_count

        except Exception as e:
            logger.error(f"Tenant cache invalidation error: {e}")
            return 0

    async def get_or_set(
        self,
        key: str,
        factory_func: Callable[[], Any],
        ttl: Optional[int] = None,
        tenant_id: Optional[str] = None
    ) -> Any:
        """Get cached value or set it using factory function."""
        # Try to get existing value
        value = await self.get(key, tenant_id)
        if value is not None:
            return value

        # Generate new value
        try:
            if asyncio.iscoroutinefunction(factory_func):
                new_value = await factory_func()
            else:
                new_value = factory_func()

            # Cache the new value
            await self.set(key, new_value, ttl, tenant_id)
            return new_value

        except Exception as e:
            logger.error(f"Factory function error in get_or_set: {e}")
            raise

    def _is_expired(self, cache_item: CacheItem) -> bool:
        """Check if cache item is expired."""
        if not cache_item.expires_at:
            return False
        return datetime.utcnow() > cache_item.expires_at

    async def _evict_lru_items(self, count: int = 1):
        """Evict least recently used items from memory cache."""
        if not self._memory_cache:
            return

        # Sort by last accessed time and evict oldest
        sorted_items = sorted(
            self._memory_cache.items(),
            key=lambda x: x[1].last_accessed
        )

        for i in range(min(count, len(sorted_items))):
            key = sorted_items[i][0]
            del self._memory_cache[key]
            self._metrics.evictions += 1

    async def _cleanup_expired_items(self):
        """Background task to clean up expired items."""
        while self._initialized:
            try:
                current_time = datetime.utcnow()
                expired_keys = []

                # Find expired items in memory cache
                for key, item in self._memory_cache.items():
                    if self._is_expired(item):
                        expired_keys.append(key)

                # Remove expired items
                for key in expired_keys:
                    del self._memory_cache[key]
                    self._metrics.evictions += 1

                if expired_keys:
                    logger.info(f"Cleaned up {len(expired_keys)} expired cache items")

                # Sleep for cleanup interval
                await asyncio.sleep(300)  # 5 minutes

            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(60)

    async def _update_metrics_periodically(self):
        """Background task to update metrics."""
        while self._initialized:
            try:
                # Update memory usage
                total_bytes = sum(item.size_bytes for item in self._memory_cache.values())
                self._metrics.memory_usage_bytes = total_bytes

                # Update tenant distribution
                tenant_dist = {}
                for item in self._memory_cache.values():
                    tenant_dist[item.tenant_id] = tenant_dist.get(item.tenant_id, 0) + 1
                self._metrics.tenant_distribution = tenant_dist

                self._metrics.last_updated = datetime.utcnow()

                await asyncio.sleep(60)  # Update every minute

            except Exception as e:
                logger.error(f"Metrics update error: {e}")
                await asyncio.sleep(60)

    def _update_set_metrics(self, tenant_id: str, size_bytes: int, operation_time: float):
        """Update metrics for set operations."""
        # Update tenant distribution
        self._metrics.tenant_distribution[tenant_id] = (
            self._metrics.tenant_distribution.get(tenant_id, 0) + 1
        )

    def _update_lookup_metrics(self, lookup_time: float):
        """Update lookup time metrics."""
        current_avg = self._metrics.avg_lookup_time_ms
        total_ops = self._metrics.hits + self._metrics.misses

        if total_ops == 1:
            self._metrics.avg_lookup_time_ms = lookup_time * 1000
        else:
            self._metrics.avg_lookup_time_ms = (
                (current_avg * (total_ops - 1) + lookup_time * 1000) / total_ops
            )

    async def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive cache metrics."""
        return {
            "performance": {
                "hit_ratio": self._metrics.hit_ratio,
                "hits": self._metrics.hits,
                "misses": self._metrics.misses,
                "evictions": self._metrics.evictions,
                "avg_lookup_time_ms": self._metrics.avg_lookup_time_ms,
            },
            "memory": {
                "items_count": len(self._memory_cache),
                "max_items": self._max_memory_items,
                "memory_usage_bytes": self._metrics.memory_usage_bytes,
                "memory_usage_mb": self._metrics.memory_usage_bytes / (1024 * 1024),
            },
            "tenant_distribution": self._metrics.tenant_distribution,
            "redis_status": "connected" if self.redis_client else "disconnected",
            "cluster_mode": self.redis_cluster,
            "last_updated": self._metrics.last_updated.isoformat(),
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on cache systems."""
        health_status = {
            "memory_cache": "healthy",
            "redis_cache": "unknown",
            "overall": "healthy"
        }

        # Check Redis health
        if self.redis_client:
            try:
                await self.redis_client.ping()
                health_status["redis_cache"] = "healthy"
            except Exception as e:
                health_status["redis_cache"] = f"unhealthy: {e}"
                health_status["overall"] = "degraded"
        else:
            health_status["redis_cache"] = "disabled"

        # Check memory cache health
        if len(self._memory_cache) >= self._max_memory_items:
            health_status["memory_cache"] = "at_capacity"

        return health_status

    async def cleanup(self):
        """Clean up cache manager resources."""
        try:
            self._initialized = False

            # Cancel background tasks
            if self._cleanup_task:
                self._cleanup_task.cancel()
            if self._metrics_task:
                self._metrics_task.cancel()

            # Close Redis connections
            if self.redis_client:
                await self.redis_client.close()

            # Clear memory cache
            self._memory_cache.clear()

            logger.info("Tenant cache manager cleaned up successfully")

        except Exception as e:
            logger.error(f"Cache manager cleanup error: {e}")

# Global tenant cache manager instance
tenant_cache_manager = TenantCacheManager()

# Convenience functions
async def init_tenant_cache() -> bool:
    """Initialize the tenant cache manager."""
    return await tenant_cache_manager.initialize()

async def close_tenant_cache():
    """Close the tenant cache manager."""
    await tenant_cache_manager.cleanup()