"""
Comprehensive performance optimization suite integration for HERMES.

This module provides a unified interface to all performance optimization components
and coordinates their initialization, monitoring, and management.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ..config import settings
from ..database.optimized_connection import (
    optimized_db_manager,
    init_optimized_database,
    close_optimized_database
)
from ..cache.tenant_cache_manager import (
    tenant_cache_manager,
    init_tenant_cache,
    close_tenant_cache
)
from ..monitoring.enhanced_metrics import (
    metrics_collector,
    initialize_enhanced_metrics,
    cleanup_enhanced_metrics
)
from ..scaling.auto_scaler import (
    auto_scaler,
    initialize_auto_scaler,
    cleanup_auto_scaler
)
from ..optimization.memory_manager import (
    memory_manager,
    initialize_memory_manager,
    cleanup_memory_manager
)
from ..tenancy.isolation_manager import (
    tenant_isolation_manager,
    initialize_tenant_isolation,
    cleanup_tenant_isolation
)
from ..performance.advanced_benchmarks import (
    benchmark_suite,
    run_comprehensive_benchmarks
)

logger = logging.getLogger(__name__)

@dataclass
class PerformanceStatus:
    """Overall performance system status."""
    initialized: bool = False
    components_status: Dict[str, str] = field(default_factory=dict)
    performance_score: float = 0.0
    last_optimization: Optional[datetime] = None
    total_optimizations: int = 0
    errors: List[str] = field(default_factory=list)

class PerformanceOptimizationSuite:
    """Unified performance optimization suite for HERMES."""

    def __init__(self):
        self.status = PerformanceStatus()
        self._optimization_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._benchmark_task: Optional[asyncio.Task] = None

        # Component managers
        self.components = {
            "database": optimized_db_manager,
            "cache": tenant_cache_manager,
            "metrics": metrics_collector,
            "auto_scaler": auto_scaler,
            "memory_manager": memory_manager,
            "tenant_isolation": tenant_isolation_manager
        }

    async def initialize(self) -> bool:
        """Initialize all performance optimization components."""
        logger.info("Initializing HERMES Performance Optimization Suite...")

        try:
            self.status.components_status = {}
            initialization_results = []

            # Initialize components in dependency order
            component_init_functions = [
                ("database", init_optimized_database),
                ("cache", init_tenant_cache),
                ("metrics", initialize_enhanced_metrics),
                ("memory_manager", initialize_memory_manager),
                ("tenant_isolation", initialize_tenant_isolation),
                ("auto_scaler", initialize_auto_scaler)
            ]

            for component_name, init_func in component_init_functions:
                try:
                    logger.info(f"Initializing {component_name}...")
                    success = await init_func()

                    if success:
                        self.status.components_status[component_name] = "healthy"
                        logger.info(f"✓ {component_name} initialized successfully")
                    else:
                        self.status.components_status[component_name] = "failed"
                        logger.error(f"✗ {component_name} initialization failed")

                    initialization_results.append((component_name, success))

                except Exception as e:
                    logger.error(f"✗ {component_name} initialization error: {e}")
                    self.status.components_status[component_name] = "error"
                    self.status.errors.append(f"{component_name}: {str(e)}")
                    initialization_results.append((component_name, False))

            # Check if critical components are running
            critical_components = ["database", "metrics"]
            critical_failures = [name for name, success in initialization_results
                               if name in critical_components and not success]

            if critical_failures:
                logger.error(f"Critical components failed: {critical_failures}")
                self.status.initialized = False
                return False

            # Start background tasks
            await self._start_background_tasks()

            # Calculate initial performance score
            self.status.performance_score = await self._calculate_performance_score()

            self.status.initialized = True
            successful_components = sum(1 for _, success in initialization_results if success)
            total_components = len(initialization_results)

            logger.info(
                f"Performance Optimization Suite initialized: "
                f"{successful_components}/{total_components} components ready"
            )

            return True

        except Exception as e:
            logger.error(f"Performance suite initialization failed: {e}")
            self.status.errors.append(f"Suite initialization: {str(e)}")
            return False

    async def _start_background_tasks(self):
        """Start background monitoring and optimization tasks."""
        try:
            self._optimization_task = asyncio.create_task(self._run_periodic_optimizations())
            self._health_check_task = asyncio.create_task(self._run_health_monitoring())
            self._benchmark_task = asyncio.create_task(self._run_periodic_benchmarks())

            logger.info("Background performance tasks started")

        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")

    async def _run_periodic_optimizations(self):
        """Run periodic performance optimizations."""
        optimization_interval = 300  # 5 minutes

        while self.status.initialized:
            try:
                logger.info("Running periodic performance optimizations...")

                # Memory optimization
                if "memory_manager" in self.status.components_status:
                    memory_result = await memory_manager.optimize_memory()
                    if memory_result.success:
                        logger.info(f"Memory optimization freed {memory_result.freed_bytes / 1024 / 1024:.1f}MB")

                # Database optimization
                if "database" in self.status.components_status:
                    db_metrics = await optimized_db_manager.get_performance_metrics()
                    logger.debug(f"Database metrics: {db_metrics}")

                # Cache optimization
                if "cache" in self.status.components_status:
                    cache_metrics = await tenant_cache_manager.get_metrics()
                    logger.debug(f"Cache hit ratio: {cache_metrics['performance']['hit_ratio']:.2f}")

                # Update performance score
                self.status.performance_score = await self._calculate_performance_score()
                self.status.last_optimization = datetime.utcnow()
                self.status.total_optimizations += 1

                await asyncio.sleep(optimization_interval)

            except Exception as e:
                logger.error(f"Periodic optimization error: {e}")
                await asyncio.sleep(optimization_interval)

    async def _run_health_monitoring(self):
        """Run periodic health checks on all components."""
        health_check_interval = 60  # 1 minute

        while self.status.initialized:
            try:
                await self._update_component_health()
                await asyncio.sleep(health_check_interval)

            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(health_check_interval)

    async def _update_component_health(self):
        """Update health status for all components."""
        try:
            # Check database health
            if optimized_db_manager._initialized:
                db_health = await optimized_db_manager.health_check()
                if db_health.get("overall") == "healthy":
                    self.status.components_status["database"] = "healthy"
                else:
                    self.status.components_status["database"] = "degraded"

            # Check cache health
            if tenant_cache_manager._initialized:
                cache_health = await tenant_cache_manager.health_check()
                if cache_health.get("overall") == "healthy":
                    self.status.components_status["cache"] = "healthy"
                else:
                    self.status.components_status["cache"] = "degraded"

            # Check auto-scaler health
            if auto_scaler._initialized:
                scaler_status = await auto_scaler.get_scaling_status()
                if scaler_status.get("scaling", {}).get("scaling_enabled"):
                    self.status.components_status["auto_scaler"] = "healthy"
                else:
                    self.status.components_status["auto_scaler"] = "inactive"

            # Check memory manager health
            if memory_manager._initialized:
                memory_status = memory_manager.get_memory_status()
                pressure = memory_status.get("current_usage", {}).get("pressure_level", "unknown")
                if pressure in ["low", "moderate"]:
                    self.status.components_status["memory_manager"] = "healthy"
                else:
                    self.status.components_status["memory_manager"] = "under_pressure"

            # Check tenant isolation health
            if tenant_isolation_manager._initialized:
                tenant_status = tenant_isolation_manager.get_all_tenants_status()
                if tenant_status.get("monitoring_status") == "active":
                    self.status.components_status["tenant_isolation"] = "healthy"
                else:
                    self.status.components_status["tenant_isolation"] = "inactive"

        except Exception as e:
            logger.error(f"Component health update error: {e}")

    async def _run_periodic_benchmarks(self):
        """Run periodic performance benchmarks."""
        benchmark_interval = 3600  # 1 hour

        while self.status.initialized:
            try:
                # Only run benchmarks in non-production environments
                if settings.debug or settings.demo_mode:
                    logger.info("Running periodic performance benchmarks...")

                    # Run lightweight benchmarks
                    from ..performance.advanced_benchmarks import BenchmarkConfig, BenchmarkType

                    quick_benchmarks = [
                        BenchmarkConfig("Quick HTTP Test", BenchmarkType.HTTP_LOAD,
                                      duration_seconds=30, concurrent_users=5),
                        BenchmarkConfig("Memory Test", BenchmarkType.MEMORY_STRESS,
                                      duration_seconds=30, concurrent_users=2),
                        BenchmarkConfig("Cache Test", BenchmarkType.CACHE_THROUGHPUT,
                                      duration_seconds=30, concurrent_users=3)
                    ]

                    for config in quick_benchmarks:
                        try:
                            result = await benchmark_suite.run_benchmark(config)
                            logger.info(f"Benchmark {config.name}: {result.success_rate:.1f}% success rate")
                        except Exception as e:
                            logger.error(f"Benchmark {config.name} failed: {e}")

                await asyncio.sleep(benchmark_interval)

            except Exception as e:
                logger.error(f"Periodic benchmarks error: {e}")
                await asyncio.sleep(benchmark_interval)

    async def _calculate_performance_score(self) -> float:
        """Calculate overall performance score (0-100)."""
        try:
            scores = []
            weights = []

            # Database performance score
            if self.status.components_status.get("database") == "healthy":
                db_metrics = await optimized_db_manager.get_performance_metrics()
                query_metrics = db_metrics.get("query_metrics", {})
                avg_query_time = query_metrics.get("avg_query_time_ms", 0)

                # Score based on average query time (lower is better)
                db_score = max(0, 100 - (avg_query_time / 10))  # 100ms = 90 score
                scores.append(db_score)
                weights.append(0.3)

            # Cache performance score
            if self.status.components_status.get("cache") == "healthy":
                cache_metrics = await tenant_cache_manager.get_metrics()
                hit_ratio = cache_metrics.get("performance", {}).get("hit_ratio", 0)

                cache_score = hit_ratio * 100
                scores.append(cache_score)
                weights.append(0.2)

            # Memory performance score
            if self.status.components_status.get("memory_manager") in ["healthy", "under_pressure"]:
                memory_status = memory_manager.get_memory_status()
                pressure_level = memory_status.get("current_usage", {}).get("pressure_level", "low")

                pressure_scores = {
                    "low": 100,
                    "moderate": 80,
                    "high": 60,
                    "critical": 30
                }
                memory_score = pressure_scores.get(pressure_level, 50)
                scores.append(memory_score)
                weights.append(0.2)

            # Component health score
            healthy_components = sum(1 for status in self.status.components_status.values()
                                   if status == "healthy")
            total_components = len(self.status.components_status)

            if total_components > 0:
                health_score = (healthy_components / total_components) * 100
                scores.append(health_score)
                weights.append(0.3)

            # Calculate weighted average
            if scores and weights:
                weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
                total_weight = sum(weights)
                return weighted_sum / total_weight
            else:
                return 50.0  # Default score when no data available

        except Exception as e:
            logger.error(f"Performance score calculation error: {e}")
            return 50.0

    async def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the entire performance suite."""
        try:
            # Collect metrics from all components
            component_metrics = {}

            if self.status.components_status.get("database") == "healthy":
                component_metrics["database"] = await optimized_db_manager.get_performance_metrics()

            if self.status.components_status.get("cache") == "healthy":
                component_metrics["cache"] = await tenant_cache_manager.get_metrics()

            if self.status.components_status.get("auto_scaler") == "healthy":
                component_metrics["auto_scaler"] = await auto_scaler.get_scaling_status()

            if self.status.components_status.get("memory_manager") in ["healthy", "under_pressure"]:
                component_metrics["memory"] = memory_manager.get_memory_status()

            if self.status.components_status.get("tenant_isolation") == "healthy":
                component_metrics["tenant_isolation"] = tenant_isolation_manager.get_all_tenants_status()

            return {
                "suite_status": {
                    "initialized": self.status.initialized,
                    "performance_score": self.status.performance_score,
                    "last_optimization": self.status.last_optimization.isoformat() if self.status.last_optimization else None,
                    "total_optimizations": self.status.total_optimizations,
                    "errors": self.status.errors[-10:]  # Last 10 errors
                },
                "component_status": self.status.components_status,
                "component_metrics": component_metrics,
                "recommendations": await self._generate_performance_recommendations()
            }

        except Exception as e:
            logger.error(f"Status collection error: {e}")
            return {
                "error": str(e),
                "suite_status": {
                    "initialized": self.status.initialized,
                    "performance_score": self.status.performance_score
                }
            }

    async def _generate_performance_recommendations(self) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        try:
            # Check database performance
            if self.status.components_status.get("database") == "healthy":
                db_metrics = await optimized_db_manager.get_performance_metrics()
                query_metrics = db_metrics.get("query_metrics", {})

                avg_query_time = query_metrics.get("avg_query_time_ms", 0)
                if avg_query_time > 100:
                    recommendations.append(
                        f"Database queries averaging {avg_query_time:.1f}ms - consider query optimization"
                    )

                cache_hit_ratio = query_metrics.get("cache_hit_ratio", 0)
                if cache_hit_ratio < 0.8:
                    recommendations.append(
                        f"Database cache hit ratio {cache_hit_ratio:.1%} - increase cache size or TTL"
                    )

            # Check memory usage
            if self.status.components_status.get("memory_manager") in ["healthy", "under_pressure"]:
                memory_status = memory_manager.get_memory_status()
                current_usage = memory_status.get("current_usage", {})

                if current_usage.get("pressure_level") in ["high", "critical"]:
                    recommendations.append("High memory pressure - consider increasing memory or optimizing usage")

                if current_usage.get("gc_objects", 0) > 100000:
                    recommendations.append("High object count - review object lifecycle management")

            # Check cache performance
            if self.status.components_status.get("cache") == "healthy":
                cache_metrics = await tenant_cache_manager.get_metrics()
                performance = cache_metrics.get("performance", {})

                if performance.get("hit_ratio", 0) < 0.7:
                    recommendations.append("Cache hit ratio below 70% - review caching strategy")

                avg_lookup_time = performance.get("avg_lookup_time_ms", 0)
                if avg_lookup_time > 10:
                    recommendations.append(f"Cache lookup time {avg_lookup_time:.1f}ms - optimize cache implementation")

            # Check auto-scaler recommendations
            if self.status.components_status.get("auto_scaler") == "healthy":
                scaler_status = await auto_scaler.get_scaling_status()
                recent_events = scaler_status.get("recent_events", [])

                frequent_scaling = len([e for e in recent_events if e.get("success")]) > 5
                if frequent_scaling:
                    recommendations.append("Frequent scaling events - review scaling thresholds")

        except Exception as e:
            logger.error(f"Recommendations generation error: {e}")
            recommendations.append("Unable to generate recommendations due to metrics collection error")

        return recommendations

    async def run_full_optimization(self) -> Dict[str, Any]:
        """Run comprehensive optimization across all components."""
        logger.info("Running full performance optimization...")

        start_time = time.perf_counter()
        optimization_results = {}

        try:
            # Memory optimization
            if self.status.components_status.get("memory_manager") in ["healthy", "under_pressure"]:
                memory_result = await memory_manager.optimize_memory()
                optimization_results["memory"] = {
                    "freed_mb": memory_result.freed_bytes / (1024 * 1024),
                    "techniques_applied": memory_result.techniques_applied,
                    "success": memory_result.success
                }

            # Database optimization
            if self.status.components_status.get("database") == "healthy":
                # Trigger database optimization
                for tenant_id in ["demo_tenant", "enterprise_client"]:
                    try:
                        result = await optimized_db_manager.optimize_for_tenant(tenant_id)
                        optimization_results[f"database_{tenant_id}"] = result
                    except Exception as e:
                        logger.error(f"Database optimization failed for {tenant_id}: {e}")

            # Cache optimization
            if self.status.components_status.get("cache") == "healthy":
                # Clear expired cache entries
                cache_metrics_before = await tenant_cache_manager.get_metrics()
                items_before = cache_metrics_before.get("memory", {}).get("items_count", 0)

                # Cache optimization happens automatically, just report status
                cache_metrics_after = await tenant_cache_manager.get_metrics()
                items_after = cache_metrics_after.get("memory", {}).get("items_count", 0)

                optimization_results["cache"] = {
                    "items_before": items_before,
                    "items_after": items_after,
                    "items_cleaned": items_before - items_after,
                    "hit_ratio": cache_metrics_after.get("performance", {}).get("hit_ratio", 0)
                }

            # Update performance score
            self.status.performance_score = await self._calculate_performance_score()
            self.status.last_optimization = datetime.utcnow()
            self.status.total_optimizations += 1

            duration = time.perf_counter() - start_time

            logger.info(f"Full optimization completed in {duration:.2f}s")

            return {
                "success": True,
                "duration_seconds": duration,
                "performance_score": self.status.performance_score,
                "optimizations": optimization_results
            }

        except Exception as e:
            logger.error(f"Full optimization failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration_seconds": time.perf_counter() - start_time
            }

    async def run_performance_benchmarks(self) -> Dict[str, Any]:
        """Run comprehensive performance benchmarks."""
        logger.info("Running comprehensive performance benchmarks...")

        try:
            # Only run in development/demo environments
            if not (settings.debug or settings.demo_mode):
                return {
                    "error": "Benchmarks disabled in production environment",
                    "success": False
                }

            result = await run_comprehensive_benchmarks()
            return {
                "success": True,
                "benchmark_results": result
            }

        except Exception as e:
            logger.error(f"Performance benchmarks failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def cleanup(self):
        """Clean up all performance optimization components."""
        logger.info("Cleaning up Performance Optimization Suite...")

        try:
            # Cancel background tasks
            for task in [self._optimization_task, self._health_check_task, self._benchmark_task]:
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            # Clean up components in reverse dependency order
            cleanup_functions = [
                ("auto_scaler", cleanup_auto_scaler),
                ("tenant_isolation", cleanup_tenant_isolation),
                ("memory_manager", cleanup_memory_manager),
                ("metrics", cleanup_enhanced_metrics),
                ("cache", close_tenant_cache),
                ("database", close_optimized_database)
            ]

            for component_name, cleanup_func in cleanup_functions:
                try:
                    await cleanup_func()
                    logger.info(f"✓ {component_name} cleaned up")
                except Exception as e:
                    logger.error(f"✗ {component_name} cleanup error: {e}")

            self.status.initialized = False
            logger.info("Performance Optimization Suite cleanup completed")

        except Exception as e:
            logger.error(f"Performance suite cleanup failed: {e}")

# Global performance optimization suite instance
performance_suite = PerformanceOptimizationSuite()

# Convenience functions
async def initialize_performance_suite() -> bool:
    """Initialize the complete performance optimization suite."""
    return await performance_suite.initialize()

async def cleanup_performance_suite():
    """Clean up the performance optimization suite."""
    await performance_suite.cleanup()

async def get_performance_status() -> Dict[str, Any]:
    """Get comprehensive performance status."""
    return await performance_suite.get_comprehensive_status()

async def optimize_performance() -> Dict[str, Any]:
    """Run full performance optimization."""
    return await performance_suite.run_full_optimization()

async def benchmark_performance() -> Dict[str, Any]:
    """Run performance benchmarks."""
    return await performance_suite.run_performance_benchmarks()