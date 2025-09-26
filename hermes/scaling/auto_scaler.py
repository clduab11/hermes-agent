"""
Enterprise-grade auto-scaling and resource optimization system for HERMES.
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

import psutil
import httpx

from ..config import settings
from ..monitoring.enhanced_metrics import metrics_collector

logger = logging.getLogger(__name__)

class ScalingDirection(Enum):
    """Scaling direction options."""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"

class ResourceType(Enum):
    """Resource types for scaling decisions."""
    CPU = "cpu"
    MEMORY = "memory"
    CONNECTIONS = "connections"
    REQUESTS_PER_SECOND = "rps"
    DATABASE_CONNECTIONS = "db_connections"
    CACHE_HIT_RATIO = "cache_hit_ratio"

class MemoryPressureLevel(Enum):
    """Memory pressure levels for scaling decisions."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ScalingRule:
    """Configuration for scaling rules."""
    name: str
    resource_type: ResourceType
    scale_up_threshold: float
    scale_down_threshold: float
    min_instances: int = 1
    max_instances: int = 10
    cooldown_seconds: int = 300
    evaluation_window_seconds: int = 60
    enabled: bool = True

@dataclass
class ScalingMetrics:
    """Current scaling metrics."""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_connections: int = 0
    requests_per_second: float = 0.0
    database_connections: int = 0
    cache_hit_ratio: float = 0.0
    response_time_p95: float = 0.0
    error_rate: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ScalingEvent:
    """Record of scaling events."""
    timestamp: datetime
    direction: ScalingDirection
    rule_name: str
    from_instances: int
    to_instances: int
    reason: str
    success: bool
    error_message: Optional[str] = None

class AutoScaler:
    """Enterprise auto-scaling and resource optimization system."""

    def __init__(self):
        self.current_instances = 1
        self.target_instances = 1

        # Scaling rules configuration
        self.scaling_rules: List[ScalingRule] = [
            ScalingRule(
                name="cpu_scaling",
                resource_type=ResourceType.CPU,
                scale_up_threshold=70.0,
                scale_down_threshold=30.0,
                max_instances=20,
                cooldown_seconds=300
            ),
            ScalingRule(
                name="memory_scaling",
                resource_type=ResourceType.MEMORY,
                scale_up_threshold=80.0,
                scale_down_threshold=40.0,
                max_instances=15,
                cooldown_seconds=300
            ),
            ScalingRule(
                name="connection_scaling",
                resource_type=ResourceType.CONNECTIONS,
                scale_up_threshold=80.0,  # 80% of max connections
                scale_down_threshold=20.0,
                max_instances=25,
                cooldown_seconds=180
            ),
            ScalingRule(
                name="rps_scaling",
                resource_type=ResourceType.REQUESTS_PER_SECOND,
                scale_up_threshold=100.0,  # 100 RPS per instance
                scale_down_threshold=25.0,
                max_instances=30,
                cooldown_seconds=120
            ),
            ScalingRule(
                name="database_scaling",
                resource_type=ResourceType.DATABASE_CONNECTIONS,
                scale_up_threshold=15.0,  # 15 connections per instance
                scale_down_threshold=5.0,
                max_instances=10,
                cooldown_seconds=300
            )
        ]

        # Metrics tracking
        self._metrics_history: List[ScalingMetrics] = []
        self._scaling_events: List[ScalingEvent] = []
        self._last_scaling_time: Dict[str, datetime] = {}

        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._scaling_task: Optional[asyncio.Task] = None
        self._optimization_task: Optional[asyncio.Task] = None

        self._initialized = False

        # Resource optimization settings
        self.gc_threshold_memory_mb = 1000  # Trigger GC at 1GB
        self.cache_cleanup_threshold = 0.9  # Clean cache at 90% capacity

    async def initialize(self) -> bool:
        """Initialize the auto-scaler system."""
        try:
            # Detect current deployment environment
            deployment_info = await self._detect_deployment_environment()
            logger.info(f"Detected deployment environment: {deployment_info}")

            # Start background monitoring tasks
            self._monitoring_task = asyncio.create_task(self._monitor_metrics())
            self._scaling_task = asyncio.create_task(self._evaluate_scaling())
            self._optimization_task = asyncio.create_task(self._optimize_resources())

            self._initialized = True
            logger.info("Auto-scaler system initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize auto-scaler: {e}")
            return False

    async def _detect_deployment_environment(self) -> Dict[str, Any]:
        """Detect the current deployment environment and capabilities."""
        environment_info = {
            "platform": "unknown",
            "container_runtime": None,
            "orchestrator": None,
            "scaling_supported": False
        }

        try:
            # Check for Kubernetes environment
            if await self._check_kubernetes():
                environment_info.update({
                    "platform": "kubernetes",
                    "orchestrator": "kubernetes",
                    "scaling_supported": True
                })

            # Check for Docker environment
            elif await self._check_docker():
                environment_info.update({
                    "platform": "docker",
                    "container_runtime": "docker",
                    "scaling_supported": False  # Docker Swarm could enable this
                })

            # Check for cloud platforms
            cloud_provider = await self._detect_cloud_provider()
            if cloud_provider:
                environment_info["cloud_provider"] = cloud_provider
                environment_info["scaling_supported"] = True

        except Exception as e:
            logger.warning(f"Environment detection error: {e}")

        return environment_info

    async def _check_kubernetes(self) -> bool:
        """Check if running in Kubernetes environment."""
        try:
            # Check for Kubernetes service account
            import os
            return (
                os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount") or
                "KUBERNETES_SERVICE_HOST" in os.environ
            )
        except:
            return False

    async def _check_docker(self) -> bool:
        """Check if running in Docker container."""
        try:
            # Check for Docker-specific files
            import os
            return (
                os.path.exists("/.dockerenv") or
                os.path.exists("/proc/1/cgroup") and "docker" in open("/proc/1/cgroup").read()
            )
        except:
            return False

    async def _detect_cloud_provider(self) -> Optional[str]:
        """Detect cloud provider from metadata services."""
        providers = {
            "aws": "http://169.254.169.254/latest/meta-data/",
            "gcp": "http://metadata.google.internal/computeMetadata/v1/",
            "azure": "http://169.254.169.254/metadata/instance"
        }

        for provider, url in providers.items():
            try:
                async with httpx.AsyncClient(timeout=2) as client:
                    headers = {"Metadata-Flavor": "Google"} if provider == "gcp" else {}
                    response = await client.get(url, headers=headers)
                    if response.status_code == 200:
                        return provider
            except:
                continue

        return None

    async def _monitor_metrics(self):
        """Background task to monitor scaling metrics."""
        while self._initialized:
            try:
                current_metrics = await self._collect_current_metrics()

                # Add to history
                self._metrics_history.append(current_metrics)

                # Keep only last hour of metrics
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                self._metrics_history = [
                    m for m in self._metrics_history if m.timestamp > cutoff_time
                ]

                # Update Prometheus metrics
                metrics_collector.update_cache_metrics(
                    cache_type="application",
                    hit_ratio=current_metrics.cache_hit_ratio,
                    items_count=0,  # Would be populated from actual cache
                    memory_usage=int(current_metrics.memory_usage * 1024 * 1024)
                )

                await asyncio.sleep(30)  # Collect metrics every 30 seconds

            except Exception as e:
                logger.error(f"Metrics monitoring error: {e}")
                await asyncio.sleep(60)

    async def _collect_current_metrics(self) -> ScalingMetrics:
        """Collect current system metrics for scaling decisions."""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Application metrics (would be integrated with actual monitoring)
            active_connections = 0  # From WebSocket handler
            requests_per_second = self._calculate_rps()
            database_connections = 0  # From database manager
            cache_hit_ratio = 0.8  # From cache manager
            response_time_p95 = 0.5  # From metrics
            error_rate = 0.01  # From error tracking

            return ScalingMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory_percent,
                active_connections=active_connections,
                requests_per_second=requests_per_second,
                database_connections=database_connections,
                cache_hit_ratio=cache_hit_ratio,
                response_time_p95=response_time_p95,
                error_rate=error_rate
            )

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return ScalingMetrics()

    def _calculate_rps(self) -> float:
        """Calculate requests per second from recent metrics."""
        if len(self._metrics_history) < 2:
            return 0.0

        # Simple RPS calculation from metrics history
        recent_window = self._metrics_history[-10:]  # Last 5 minutes
        if len(recent_window) < 2:
            return 0.0

        # This would be calculated from actual request metrics
        return 50.0  # Placeholder

    async def _evaluate_scaling(self):
        """Background task to evaluate scaling decisions."""
        while self._initialized:
            try:
                if len(self._metrics_history) < 3:
                    await asyncio.sleep(60)
                    continue

                current_metrics = self._metrics_history[-1]
                scaling_decision = await self._make_scaling_decision(current_metrics)

                if scaling_decision != ScalingDirection.STABLE:
                    await self._execute_scaling(scaling_decision, current_metrics)

                await asyncio.sleep(60)  # Evaluate every minute

            except Exception as e:
                logger.error(f"Scaling evaluation error: {e}")
                await asyncio.sleep(120)

    async def _make_scaling_decision(self, current_metrics: ScalingMetrics) -> ScalingDirection:
        """Make scaling decision based on current metrics."""
        scale_up_votes = 0
        scale_down_votes = 0
        total_rules = 0

        for rule in self.scaling_rules:
            if not rule.enabled:
                continue

            # Check cooldown
            if self._is_in_cooldown(rule):
                continue

            total_rules += 1
            metric_value = self._get_metric_value(current_metrics, rule.resource_type)

            if metric_value > rule.scale_up_threshold:
                scale_up_votes += 1
            elif metric_value < rule.scale_down_threshold:
                scale_down_votes += 1

        # Decision logic
        if total_rules == 0:
            return ScalingDirection.STABLE

        # Require majority vote for scaling decisions
        vote_threshold = max(1, total_rules // 2)

        if scale_up_votes >= vote_threshold and self.current_instances < self._get_max_instances():
            return ScalingDirection.UP
        elif scale_down_votes >= vote_threshold and self.current_instances > self._get_min_instances():
            return ScalingDirection.DOWN
        else:
            return ScalingDirection.STABLE

    def _get_metric_value(self, metrics: ScalingMetrics, resource_type: ResourceType) -> float:
        """Get metric value for specific resource type."""
        if resource_type == ResourceType.CPU:
            return metrics.cpu_usage
        elif resource_type == ResourceType.MEMORY:
            return metrics.memory_usage
        elif resource_type == ResourceType.CONNECTIONS:
            return metrics.active_connections
        elif resource_type == ResourceType.REQUESTS_PER_SECOND:
            return metrics.requests_per_second
        elif resource_type == ResourceType.DATABASE_CONNECTIONS:
            return metrics.database_connections
        elif resource_type == ResourceType.CACHE_HIT_RATIO:
            return (1.0 - metrics.cache_hit_ratio) * 100  # Invert for scaling logic
        else:
            return 0.0

    def _is_in_cooldown(self, rule: ScalingRule) -> bool:
        """Check if rule is in cooldown period."""
        last_scaling = self._last_scaling_time.get(rule.name)
        if not last_scaling:
            return False

        cooldown_end = last_scaling + timedelta(seconds=rule.cooldown_seconds)
        return datetime.utcnow() < cooldown_end

    def _get_max_instances(self) -> int:
        """Get maximum instances across all rules."""
        return max(rule.max_instances for rule in self.scaling_rules)

    def _get_min_instances(self) -> int:
        """Get minimum instances across all rules."""
        return max(rule.min_instances for rule in self.scaling_rules)

    async def _execute_scaling(self, direction: ScalingDirection, metrics: ScalingMetrics):
        """Execute scaling decision."""
        try:
            original_instances = self.current_instances

            if direction == ScalingDirection.UP:
                self.target_instances = min(
                    self.current_instances + self._calculate_scale_amount(metrics, direction),
                    self._get_max_instances()
                )
            else:  # ScalingDirection.DOWN
                self.target_instances = max(
                    self.current_instances - self._calculate_scale_amount(metrics, direction),
                    self._get_min_instances()
                )

            if self.target_instances == self.current_instances:
                return  # No scaling needed

            success = await self._perform_scaling(direction, self.target_instances)

            # Record scaling event
            event = ScalingEvent(
                timestamp=datetime.utcnow(),
                direction=direction,
                rule_name="composite",
                from_instances=original_instances,
                to_instances=self.target_instances if success else original_instances,
                reason=f"Metrics: CPU={metrics.cpu_usage:.1f}%, Memory={metrics.memory_usage:.1f}%",
                success=success
            )

            self._scaling_events.append(event)

            if success:
                self.current_instances = self.target_instances
                logger.info(f"Scaled {direction.value}: {original_instances} -> {self.current_instances} instances")
            else:
                logger.error(f"Failed to scale {direction.value}")

            # Update cooldown times
            for rule in self.scaling_rules:
                self._last_scaling_time[rule.name] = datetime.utcnow()

        except Exception as e:
            logger.error(f"Scaling execution error: {e}")

    def _calculate_scale_amount(self, metrics: ScalingMetrics, direction: ScalingDirection) -> int:
        """Calculate how many instances to scale by."""
        # Simple scaling strategy - more sophisticated algorithms could be used
        if direction == ScalingDirection.UP:
            # Scale more aggressively under high load
            if metrics.cpu_usage > 90 or metrics.memory_usage > 90:
                return max(2, self.current_instances // 2)  # Scale by 50%
            else:
                return max(1, self.current_instances // 4)  # Scale by 25%
        else:  # ScalingDirection.DOWN
            # Scale down conservatively
            return 1

    async def _perform_scaling(self, direction: ScalingDirection, target_instances: int) -> bool:
        """Perform the actual scaling operation."""
        try:
            # This would integrate with the actual deployment platform
            # For now, we'll simulate scaling

            if await self._check_kubernetes():
                return await self._scale_kubernetes(target_instances)
            elif await self._detect_cloud_provider():
                return await self._scale_cloud_platform(target_instances)
            else:
                # Local/single instance - simulate scaling
                logger.info(f"Simulated scaling to {target_instances} instances")
                return True

        except Exception as e:
            logger.error(f"Scaling operation failed: {e}")
            return False

    async def _scale_kubernetes(self, target_instances: int) -> bool:
        """Scale Kubernetes deployment."""
        try:
            # This would use the Kubernetes API
            logger.info(f"Scaling Kubernetes deployment to {target_instances} replicas")
            # kubectl scale deployment hermes-agent --replicas={target_instances}
            return True
        except Exception as e:
            logger.error(f"Kubernetes scaling failed: {e}")
            return False

    async def _scale_cloud_platform(self, target_instances: int) -> bool:
        """Scale cloud platform deployment."""
        try:
            # This would use cloud provider APIs
            logger.info(f"Scaling cloud deployment to {target_instances} instances")
            return True
        except Exception as e:
            logger.error(f"Cloud scaling failed: {e}")
            return False

    async def _optimize_resources(self):
        """Background task for resource optimization."""
        while self._initialized:
            try:
                await self._perform_memory_optimization()
                await self._perform_cache_optimization()
                await self._perform_database_optimization()

                await asyncio.sleep(300)  # Optimize every 5 minutes

            except Exception as e:
                logger.error(f"Resource optimization error: {e}")
                await asyncio.sleep(600)

    async def _perform_memory_optimization(self):
        """Perform memory optimization tasks."""
        try:
            import gc
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)

            if memory_mb > self.gc_threshold_memory_mb:
                logger.info(f"Triggering garbage collection at {memory_mb:.1f}MB memory usage")

                # Force garbage collection
                collected = gc.collect()

                # Log results
                new_memory = psutil.virtual_memory()
                freed_mb = (memory.used - new_memory.used) / (1024 * 1024)

                logger.info(f"Garbage collection freed {freed_mb:.1f}MB, collected {collected} objects")

                # Update metrics
                metrics_collector.record_exception("memory_optimization", "auto_scaler")

        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")

    async def _perform_cache_optimization(self):
        """Perform cache optimization tasks."""
        try:
            # This would integrate with the cache manager
            logger.debug("Performing cache optimization")

            # Example cache optimization tasks:
            # - Remove expired entries
            # - Evict least recently used items
            # - Compress cache data
            # - Rebalance cache across nodes

        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")

    async def _perform_database_optimization(self):
        """Perform database optimization tasks."""
        try:
            # This would integrate with the database manager
            logger.debug("Performing database optimization")

            # Example database optimization tasks:
            # - Close idle connections
            # - Update connection pool settings
            # - Clear query caches if needed
            # - Analyze slow queries

        except Exception as e:
            logger.error(f"Database optimization failed: {e}")

    async def get_scaling_status(self) -> Dict[str, Any]:
        """Get current scaling status and metrics."""
        current_metrics = self._metrics_history[-1] if self._metrics_history else ScalingMetrics()

        return {
            "scaling": {
                "current_instances": self.current_instances,
                "target_instances": self.target_instances,
                "scaling_enabled": self._initialized
            },
            "metrics": {
                "cpu_usage": current_metrics.cpu_usage,
                "memory_usage": current_metrics.memory_usage,
                "active_connections": current_metrics.active_connections,
                "requests_per_second": current_metrics.requests_per_second,
                "cache_hit_ratio": current_metrics.cache_hit_ratio,
                "error_rate": current_metrics.error_rate
            },
            "rules": [
                {
                    "name": rule.name,
                    "resource_type": rule.resource_type.value,
                    "scale_up_threshold": rule.scale_up_threshold,
                    "scale_down_threshold": rule.scale_down_threshold,
                    "enabled": rule.enabled,
                    "in_cooldown": self._is_in_cooldown(rule)
                }
                for rule in self.scaling_rules
            ],
            "recent_events": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "direction": event.direction.value,
                    "from_instances": event.from_instances,
                    "to_instances": event.to_instances,
                    "reason": event.reason,
                    "success": event.success
                }
                for event in self._scaling_events[-10:]  # Last 10 events
            ]
        }

    async def update_scaling_rule(self, rule_name: str, **kwargs) -> bool:
        """Update a scaling rule configuration."""
        try:
            for rule in self.scaling_rules:
                if rule.name == rule_name:
                    for key, value in kwargs.items():
                        if hasattr(rule, key):
                            setattr(rule, key, value)

                    logger.info(f"Updated scaling rule {rule_name}: {kwargs}")
                    return True

            logger.warning(f"Scaling rule {rule_name} not found")
            return False

        except Exception as e:
            logger.error(f"Failed to update scaling rule: {e}")
            return False

    async def cleanup(self):
        """Clean up auto-scaler resources."""
        try:
            self._initialized = False

            # Cancel background tasks
            for task in [self._monitoring_task, self._scaling_task, self._optimization_task]:
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            logger.info("Auto-scaler system cleaned up successfully")

        except Exception as e:
            logger.error(f"Auto-scaler cleanup error: {e}")

# Global auto-scaler instance
auto_scaler = AutoScaler()

# Convenience functions
async def initialize_auto_scaler() -> bool:
    """Initialize the auto-scaler system."""
    return await auto_scaler.initialize()

async def cleanup_auto_scaler():
    """Clean up the auto-scaler system."""
    await auto_scaler.cleanup()

async def get_scaling_status() -> Dict[str, Any]:
    """Get current scaling status."""
    return await auto_scaler.get_scaling_status()