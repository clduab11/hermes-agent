"""
Advanced tenant isolation and multi-tenancy optimization system for HERMES.
"""

import asyncio
import logging
import time
import hashlib
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from contextlib import asynccontextmanager

import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database.tenant_context import TenantContext, get_current_tenant, set_tenant_context
from ..monitoring.enhanced_metrics import metrics_collector
from ..cache.tenant_cache_manager import tenant_cache_manager

logger = logging.getLogger(__name__)

class TenantTier(Enum):
    """Tenant service tiers."""
    FREE = "free"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class IsolationLevel(Enum):
    """Levels of tenant isolation."""
    SHARED = "shared"          # Shared resources with logical separation
    DEDICATED = "dedicated"    # Dedicated resources per tenant
    HYBRID = "hybrid"         # Mix of shared and dedicated based on tier

@dataclass
class TenantResourceLimits:
    """Resource limits per tenant."""
    max_connections: int = 10
    max_memory_mb: int = 500
    max_storage_mb: int = 1000
    max_requests_per_minute: int = 1000
    max_concurrent_sessions: int = 5
    max_api_calls_per_day: int = 10000
    cache_quota_mb: int = 100
    database_query_timeout_seconds: int = 30

@dataclass
class TenantMetrics:
    """Performance and usage metrics per tenant."""
    tenant_id: str
    connections_active: int = 0
    memory_usage_mb: float = 0.0
    storage_usage_mb: float = 0.0
    requests_per_minute: int = 0
    concurrent_sessions: int = 0
    api_calls_today: int = 0
    cache_usage_mb: float = 0.0
    last_activity: datetime = field(default_factory=datetime.utcnow)
    performance_score: float = 100.0  # 0-100 scale

@dataclass
class TenantConfig:
    """Configuration for a tenant."""
    tenant_id: str
    tier: TenantTier
    isolation_level: IsolationLevel
    resource_limits: TenantResourceLimits
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    custom_settings: Dict[str, Any] = field(default_factory=dict)

class TenantIsolationManager:
    """Advanced tenant isolation and resource management system."""

    def __init__(self):
        self.tenant_configs: Dict[str, TenantConfig] = {}
        self.tenant_metrics: Dict[str, TenantMetrics] = {}
        self.tenant_namespaces: Dict[str, str] = {}  # tenant_id -> namespace
        self.redis_connections: Dict[str, redis.Redis] = {}  # Per-tenant Redis connections

        # Resource monitoring
        self._resource_monitor_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

        # Default tier configurations
        self.tier_configs = {
            TenantTier.FREE: TenantResourceLimits(
                max_connections=5,
                max_memory_mb=100,
                max_storage_mb=500,
                max_requests_per_minute=100,
                max_concurrent_sessions=2,
                max_api_calls_per_day=1000,
                cache_quota_mb=50,
                database_query_timeout_seconds=15
            ),
            TenantTier.PROFESSIONAL: TenantResourceLimits(
                max_connections=20,
                max_memory_mb=1000,
                max_storage_mb=5000,
                max_requests_per_minute=2000,
                max_concurrent_sessions=10,
                max_api_calls_per_day=50000,
                cache_quota_mb=200,
                database_query_timeout_seconds=30
            ),
            TenantTier.ENTERPRISE: TenantResourceLimits(
                max_connections=100,
                max_memory_mb=5000,
                max_storage_mb=50000,
                max_requests_per_minute=10000,
                max_concurrent_sessions=50,
                max_api_calls_per_day=1000000,
                cache_quota_mb=1000,
                database_query_timeout_seconds=60
            )
        }

        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize the tenant isolation system."""
        try:
            # Load tenant configurations
            await self._load_tenant_configurations()

            # Set up tenant namespaces
            await self._setup_tenant_namespaces()

            # Initialize per-tenant Redis connections
            await self._initialize_tenant_redis_connections()

            # Start background monitoring
            self._resource_monitor_task = asyncio.create_task(self._monitor_tenant_resources())
            self._cleanup_task = asyncio.create_task(self._cleanup_inactive_tenants())

            self._initialized = True
            logger.info("Tenant isolation system initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize tenant isolation system: {e}")
            return False

    async def _load_tenant_configurations(self):
        """Load tenant configurations from database or create defaults."""
        try:
            # For demo, create some default tenant configurations
            default_tenants = [
                ("demo_tenant", TenantTier.PROFESSIONAL),
                ("enterprise_client", TenantTier.ENTERPRISE),
                ("free_user_1", TenantTier.FREE),
            ]

            for tenant_id, tier in default_tenants:
                config = TenantConfig(
                    tenant_id=tenant_id,
                    tier=tier,
                    isolation_level=IsolationLevel.HYBRID,
                    resource_limits=self.tier_configs[tier]
                )

                self.tenant_configs[tenant_id] = config
                self.tenant_metrics[tenant_id] = TenantMetrics(tenant_id=tenant_id)

            logger.info(f"Loaded {len(self.tenant_configs)} tenant configurations")

        except Exception as e:
            logger.error(f"Failed to load tenant configurations: {e}")

    async def _setup_tenant_namespaces(self):
        """Set up isolated namespaces for tenants."""
        try:
            for tenant_id in self.tenant_configs.keys():
                # Create deterministic namespace based on tenant ID
                namespace_hash = hashlib.sha256(tenant_id.encode()).hexdigest()[:16]
                namespace = f"tenant_{namespace_hash}"

                self.tenant_namespaces[tenant_id] = namespace

                logger.debug(f"Created namespace {namespace} for tenant {tenant_id}")

        except Exception as e:
            logger.error(f"Failed to set up tenant namespaces: {e}")

    async def _initialize_tenant_redis_connections(self):
        """Initialize per-tenant Redis connections for dedicated isolation."""
        if not settings.redis_url:
            logger.warning("Redis not configured - skipping tenant Redis setup")
            return

        try:
            for tenant_id, config in self.tenant_configs.items():
                if config.isolation_level in [IsolationLevel.DEDICATED, IsolationLevel.HYBRID]:
                    # Create dedicated Redis connection for enterprise tenants
                    if config.tier == TenantTier.ENTERPRISE:
                        # In production, this would connect to dedicated Redis instances
                        redis_client = redis.from_url(
                            settings.redis_url,
                            encoding="utf-8",
                            decode_responses=True,
                            db=hash(tenant_id) % 16,  # Use different DB number per tenant
                            max_connections=config.resource_limits.max_connections
                        )

                        await redis_client.ping()
                        self.redis_connections[tenant_id] = redis_client

                        logger.info(f"Created dedicated Redis connection for tenant {tenant_id}")

        except Exception as e:
            logger.error(f"Failed to initialize tenant Redis connections: {e}")

    async def _monitor_tenant_resources(self):
        """Background task to monitor per-tenant resource usage."""
        while self._initialized:
            try:
                for tenant_id, config in self.tenant_configs.items():
                    metrics = await self._collect_tenant_metrics(tenant_id)
                    self.tenant_metrics[tenant_id] = metrics

                    # Check for resource limit violations
                    violations = self._check_resource_violations(config, metrics)
                    if violations:
                        await self._handle_resource_violations(tenant_id, violations)

                    # Update performance score
                    performance_score = self._calculate_performance_score(metrics, config)
                    metrics.performance_score = performance_score

                    # Update Prometheus metrics
                    metrics_collector.update_tenant_metrics(
                        tenant_id=tenant_id,
                        active_users=1,  # Would be calculated from actual sessions
                        storage_usage={"database": int(metrics.storage_usage_mb * 1024 * 1024)}
                    )

                await asyncio.sleep(30)  # Monitor every 30 seconds

            except Exception as e:
                logger.error(f"Tenant resource monitoring error: {e}")
                await asyncio.sleep(60)

    async def _collect_tenant_metrics(self, tenant_id: str) -> TenantMetrics:
        """Collect current resource usage metrics for a tenant."""
        try:
            # This would integrate with actual resource monitoring
            # For now, simulate metrics collection

            current_metrics = self.tenant_metrics.get(tenant_id, TenantMetrics(tenant_id=tenant_id))

            # Simulate some realistic metrics
            import random
            current_metrics.connections_active = random.randint(0, 10)
            current_metrics.memory_usage_mb = random.uniform(50, 200)
            current_metrics.concurrent_sessions = random.randint(0, 5)
            current_metrics.requests_per_minute = random.randint(10, 100)
            current_metrics.last_activity = datetime.utcnow()

            return current_metrics

        except Exception as e:
            logger.error(f"Failed to collect metrics for tenant {tenant_id}: {e}")
            return TenantMetrics(tenant_id=tenant_id)

    def _check_resource_violations(self, config: TenantConfig, metrics: TenantMetrics) -> List[str]:
        """Check if tenant has violated any resource limits."""
        violations = []
        limits = config.resource_limits

        if metrics.connections_active > limits.max_connections:
            violations.append(f"max_connections exceeded: {metrics.connections_active}/{limits.max_connections}")

        if metrics.memory_usage_mb > limits.max_memory_mb:
            violations.append(f"max_memory exceeded: {metrics.memory_usage_mb:.1f}/{limits.max_memory_mb}MB")

        if metrics.storage_usage_mb > limits.max_storage_mb:
            violations.append(f"max_storage exceeded: {metrics.storage_usage_mb:.1f}/{limits.max_storage_mb}MB")

        if metrics.requests_per_minute > limits.max_requests_per_minute:
            violations.append(f"max_requests_per_minute exceeded: {metrics.requests_per_minute}/{limits.max_requests_per_minute}")

        if metrics.concurrent_sessions > limits.max_concurrent_sessions:
            violations.append(f"max_concurrent_sessions exceeded: {metrics.concurrent_sessions}/{limits.max_concurrent_sessions}")

        if metrics.api_calls_today > limits.max_api_calls_per_day:
            violations.append(f"max_api_calls_per_day exceeded: {metrics.api_calls_today}/{limits.max_api_calls_per_day}")

        return violations

    async def _handle_resource_violations(self, tenant_id: str, violations: List[str]):
        """Handle resource limit violations."""
        logger.warning(f"Tenant {tenant_id} resource violations: {violations}")

        config = self.tenant_configs.get(tenant_id)
        if not config:
            return

        # Apply throttling or restrictions based on tier
        if config.tier == TenantTier.FREE:
            # Strict enforcement for free tier
            await self._apply_throttling(tenant_id, severity="high")

        elif config.tier == TenantTier.PROFESSIONAL:
            # Moderate enforcement with warnings
            await self._apply_throttling(tenant_id, severity="medium")
            await self._send_usage_warning(tenant_id, violations)

        elif config.tier == TenantTier.ENTERPRISE:
            # Lenient enforcement with notifications
            await self._send_usage_notification(tenant_id, violations)

        # Update metrics
        metrics_collector.record_billing_event("resource_violation")

    async def _apply_throttling(self, tenant_id: str, severity: str = "medium"):
        """Apply throttling to a tenant's requests."""
        try:
            # This would integrate with rate limiting systems
            logger.info(f"Applying {severity} throttling to tenant {tenant_id}")

            throttle_settings = {
                "low": {"delay_ms": 100, "rejection_rate": 0.1},
                "medium": {"delay_ms": 500, "rejection_rate": 0.2},
                "high": {"delay_ms": 1000, "rejection_rate": 0.5}
            }

            settings_to_apply = throttle_settings.get(severity, throttle_settings["medium"])

            # Store throttling settings (would be used by middleware)
            cache_key = f"throttle:{tenant_id}"
            if tenant_cache_manager.redis_client:
                await tenant_cache_manager.set(
                    cache_key,
                    settings_to_apply,
                    ttl=300,  # 5 minutes
                    tenant_id=tenant_id
                )

        except Exception as e:
            logger.error(f"Failed to apply throttling to tenant {tenant_id}: {e}")

    async def _send_usage_warning(self, tenant_id: str, violations: List[str]):
        """Send usage warning to tenant."""
        logger.info(f"Sending usage warning to tenant {tenant_id}: {violations}")
        # This would integrate with notification systems

    async def _send_usage_notification(self, tenant_id: str, violations: List[str]):
        """Send usage notification to tenant."""
        logger.info(f"Sending usage notification to tenant {tenant_id}: {violations}")
        # This would integrate with notification systems

    def _calculate_performance_score(self, metrics: TenantMetrics, config: TenantConfig) -> float:
        """Calculate performance score (0-100) for a tenant."""
        try:
            score = 100.0
            limits = config.resource_limits

            # Deduct points for resource usage
            if metrics.memory_usage_mb > 0:
                memory_usage_ratio = metrics.memory_usage_mb / limits.max_memory_mb
                if memory_usage_ratio > 0.8:
                    score -= (memory_usage_ratio - 0.8) * 100

            if metrics.connections_active > 0:
                connection_usage_ratio = metrics.connections_active / limits.max_connections
                if connection_usage_ratio > 0.8:
                    score -= (connection_usage_ratio - 0.8) * 50

            if metrics.requests_per_minute > 0:
                rps_usage_ratio = metrics.requests_per_minute / limits.max_requests_per_minute
                if rps_usage_ratio > 0.8:
                    score -= (rps_usage_ratio - 0.8) * 50

            return max(0.0, min(100.0, score))

        except Exception as e:
            logger.error(f"Failed to calculate performance score: {e}")
            return 50.0  # Default score

    @asynccontextmanager
    async def tenant_database_session(self, tenant_id: str) -> AsyncSession:
        """Get a database session with tenant-specific isolation."""
        try:
            # This would integrate with the optimized database manager
            from ..database.optimized_connection import optimized_db_manager

            async with optimized_db_manager.get_session() as session:
                # Set tenant context
                tenant_context = TenantContext(tenant_id=tenant_id)
                set_tenant_context(tenant_context)

                # Apply tenant-specific query timeouts
                config = self.tenant_configs.get(tenant_id)
                if config:
                    timeout = config.resource_limits.database_query_timeout_seconds
                    await session.execute(text(f"SET statement_timeout = '{timeout}s'"))

                yield session

        except Exception as e:
            logger.error(f"Failed to create tenant database session: {e}")
            raise

    async def get_tenant_cache_client(self, tenant_id: str):
        """Get a cache client with tenant-specific isolation."""
        try:
            # Check if tenant has dedicated Redis connection
            if tenant_id in self.redis_connections:
                return self.redis_connections[tenant_id]

            # Use shared cache with tenant namespace
            return tenant_cache_manager

        except Exception as e:
            logger.error(f"Failed to get tenant cache client: {e}")
            return None

    async def _cleanup_inactive_tenants(self):
        """Background task to clean up inactive tenant resources."""
        while self._initialized:
            try:
                cutoff_time = datetime.utcnow() - timedelta(hours=24)

                for tenant_id, metrics in list(self.tenant_metrics.items()):
                    if metrics.last_activity < cutoff_time:
                        logger.info(f"Cleaning up inactive tenant: {tenant_id}")

                        # Clean up tenant-specific resources
                        await self._cleanup_tenant_resources(tenant_id)

                        # Remove from active monitoring (but keep config)
                        if tenant_id in self.tenant_metrics:
                            del self.tenant_metrics[tenant_id]

                await asyncio.sleep(3600)  # Clean up every hour

            except Exception as e:
                logger.error(f"Tenant cleanup error: {e}")
                await asyncio.sleep(3600)

    async def _cleanup_tenant_resources(self, tenant_id: str):
        """Clean up resources for an inactive tenant."""
        try:
            # Clean up cache entries
            await tenant_cache_manager.invalidate_tenant(tenant_id)

            # Close dedicated Redis connection if exists
            if tenant_id in self.redis_connections:
                await self.redis_connections[tenant_id].close()
                del self.redis_connections[tenant_id]

            # Clean up temporary files, sessions, etc.
            logger.debug(f"Cleaned up resources for tenant {tenant_id}")

        except Exception as e:
            logger.error(f"Failed to clean up resources for tenant {tenant_id}: {e}")

    async def create_tenant(
        self,
        tenant_id: str,
        tier: TenantTier = TenantTier.FREE,
        custom_limits: Optional[TenantResourceLimits] = None
    ) -> bool:
        """Create a new tenant with specified configuration."""
        try:
            if tenant_id in self.tenant_configs:
                logger.warning(f"Tenant {tenant_id} already exists")
                return False

            # Use custom limits or default for tier
            resource_limits = custom_limits or self.tier_configs[tier]

            # Determine isolation level based on tier
            isolation_level = IsolationLevel.SHARED
            if tier == TenantTier.ENTERPRISE:
                isolation_level = IsolationLevel.DEDICATED
            elif tier == TenantTier.PROFESSIONAL:
                isolation_level = IsolationLevel.HYBRID

            # Create tenant configuration
            config = TenantConfig(
                tenant_id=tenant_id,
                tier=tier,
                isolation_level=isolation_level,
                resource_limits=resource_limits
            )

            self.tenant_configs[tenant_id] = config
            self.tenant_metrics[tenant_id] = TenantMetrics(tenant_id=tenant_id)

            # Set up namespace
            namespace_hash = hashlib.sha256(tenant_id.encode()).hexdigest()[:16]
            self.tenant_namespaces[tenant_id] = f"tenant_{namespace_hash}"

            # Set up dedicated Redis connection if needed
            if isolation_level == IsolationLevel.DEDICATED and settings.redis_url:
                redis_client = redis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    db=hash(tenant_id) % 16,
                    max_connections=resource_limits.max_connections
                )

                await redis_client.ping()
                self.redis_connections[tenant_id] = redis_client

            logger.info(f"Created tenant {tenant_id} with tier {tier.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to create tenant {tenant_id}: {e}")
            return False

    async def update_tenant_tier(self, tenant_id: str, new_tier: TenantTier) -> bool:
        """Update a tenant's service tier."""
        try:
            if tenant_id not in self.tenant_configs:
                logger.error(f"Tenant {tenant_id} not found")
                return False

            old_tier = self.tenant_configs[tenant_id].tier
            self.tenant_configs[tenant_id].tier = new_tier
            self.tenant_configs[tenant_id].resource_limits = self.tier_configs[new_tier]

            # Update isolation level if needed
            if new_tier == TenantTier.ENTERPRISE:
                self.tenant_configs[tenant_id].isolation_level = IsolationLevel.DEDICATED
                # Set up dedicated Redis connection
                if tenant_id not in self.redis_connections and settings.redis_url:
                    redis_client = redis.from_url(
                        settings.redis_url,
                        encoding="utf-8",
                        decode_responses=True,
                        db=hash(tenant_id) % 16,
                        max_connections=self.tier_configs[new_tier].max_connections
                    )
                    await redis_client.ping()
                    self.redis_connections[tenant_id] = redis_client

            logger.info(f"Updated tenant {tenant_id} from {old_tier.value} to {new_tier.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to update tenant tier: {e}")
            return False

    def get_tenant_status(self, tenant_id: str) -> Dict[str, Any]:
        """Get comprehensive status for a tenant."""
        config = self.tenant_configs.get(tenant_id)
        metrics = self.tenant_metrics.get(tenant_id)

        if not config:
            return {"error": f"Tenant {tenant_id} not found"}

        return {
            "tenant_id": tenant_id,
            "tier": config.tier.value,
            "isolation_level": config.isolation_level.value,
            "enabled": config.enabled,
            "namespace": self.tenant_namespaces.get(tenant_id),
            "has_dedicated_redis": tenant_id in self.redis_connections,
            "resource_limits": {
                "max_connections": config.resource_limits.max_connections,
                "max_memory_mb": config.resource_limits.max_memory_mb,
                "max_storage_mb": config.resource_limits.max_storage_mb,
                "max_requests_per_minute": config.resource_limits.max_requests_per_minute,
                "max_concurrent_sessions": config.resource_limits.max_concurrent_sessions,
                "cache_quota_mb": config.resource_limits.cache_quota_mb
            },
            "current_usage": {
                "connections_active": metrics.connections_active if metrics else 0,
                "memory_usage_mb": metrics.memory_usage_mb if metrics else 0,
                "concurrent_sessions": metrics.concurrent_sessions if metrics else 0,
                "requests_per_minute": metrics.requests_per_minute if metrics else 0,
                "performance_score": metrics.performance_score if metrics else 100
            } if metrics else {},
            "last_activity": metrics.last_activity.isoformat() if metrics else None
        }

    def get_all_tenants_status(self) -> Dict[str, Any]:
        """Get status summary for all tenants."""
        tenants_by_tier = {tier: [] for tier in TenantTier}
        total_active_tenants = 0

        for tenant_id, config in self.tenant_configs.items():
            tenants_by_tier[config.tier].append(tenant_id)

            metrics = self.tenant_metrics.get(tenant_id)
            if metrics and metrics.last_activity > datetime.utcnow() - timedelta(hours=24):
                total_active_tenants += 1

        return {
            "total_tenants": len(self.tenant_configs),
            "active_tenants_24h": total_active_tenants,
            "tenants_by_tier": {tier.value: len(tenants) for tier, tenants in tenants_by_tier.items()},
            "isolation_levels": {
                level.value: sum(1 for config in self.tenant_configs.values() if config.isolation_level == level)
                for level in IsolationLevel
            },
            "dedicated_redis_connections": len(self.redis_connections),
            "monitoring_status": "active" if self._initialized else "inactive"
        }

    async def cleanup(self):
        """Clean up tenant isolation manager resources."""
        try:
            self._initialized = False

            # Cancel background tasks
            for task in [self._resource_monitor_task, self._cleanup_task]:
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            # Close all Redis connections
            for tenant_id, redis_client in self.redis_connections.items():
                try:
                    await redis_client.close()
                except Exception as e:
                    logger.error(f"Error closing Redis connection for tenant {tenant_id}: {e}")

            logger.info("Tenant isolation manager cleaned up successfully")

        except Exception as e:
            logger.error(f"Tenant isolation manager cleanup error: {e}")

# Global tenant isolation manager instance
tenant_isolation_manager = TenantIsolationManager()

# Convenience functions
async def initialize_tenant_isolation() -> bool:
    """Initialize the tenant isolation system."""
    return await tenant_isolation_manager.initialize()

async def cleanup_tenant_isolation():
    """Clean up the tenant isolation system."""
    await tenant_isolation_manager.cleanup()

def get_tenant_status(tenant_id: str) -> Dict[str, Any]:
    """Get status for a specific tenant."""
    return tenant_isolation_manager.get_tenant_status(tenant_id)

def get_all_tenants_status() -> Dict[str, Any]:
    """Get status for all tenants."""
    return tenant_isolation_manager.get_all_tenants_status()

# Context manager for tenant isolation
@asynccontextmanager
async def tenant_isolation_context(tenant_id: str):
    """Context manager to ensure proper tenant isolation."""
    try:
        # Set tenant context
        tenant_context = TenantContext(tenant_id=tenant_id)
        set_tenant_context(tenant_context)

        yield

    finally:
        # Clean up tenant context
        set_tenant_context(TenantContext(tenant_id="system"))