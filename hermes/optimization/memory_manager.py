"""
Advanced memory optimization and garbage collection management for HERMES.
"""

import gc
import sys
import time
import asyncio
import logging
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from weakref import WeakValueDictionary, WeakSet
from collections import defaultdict

import psutil
from pympler import tracker, muppy, summary

from ..config import settings
from ..monitoring.enhanced_metrics import metrics_collector

logger = logging.getLogger(__name__)

class MemoryPressureLevel(Enum):
    """Memory pressure levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class MemoryMetrics:
    """Memory usage metrics."""
    rss_bytes: int = 0
    vms_bytes: int = 0
    percent_used: float = 0.0
    available_bytes: int = 0
    gc_objects: int = 0
    gc_collections: List[int] = field(default_factory=list)
    large_objects_count: int = 0
    memory_leaks_detected: int = 0
    pressure_level: MemoryPressureLevel = MemoryPressureLevel.LOW
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class MemoryOptimizationResult:
    """Results from memory optimization."""
    freed_bytes: int
    objects_collected: int
    optimization_time_ms: float
    techniques_applied: List[str]
    success: bool
    error_message: Optional[str] = None

class MemoryManager:
    """Advanced memory management and optimization system."""

    def __init__(self):
        self._metrics_history: List[MemoryMetrics] = []
        self._optimization_callbacks: List[Callable] = []
        self._memory_tracker = tracker.SummaryTracker()

        # Memory thresholds (as percentages)
        self.low_pressure_threshold = 60.0
        self.moderate_pressure_threshold = 75.0
        self.high_pressure_threshold = 85.0
        self.critical_pressure_threshold = 95.0

        # Optimization settings
        self.gc_frequency_seconds = 60  # Run GC every minute under normal conditions
        self.emergency_gc_frequency_seconds = 10  # Run GC every 10s under high pressure
        self.large_object_threshold_mb = 10  # Objects larger than 10MB
        self.max_memory_history = 1000  # Keep last 1000 memory snapshots

        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._optimization_task: Optional[asyncio.Task] = None
        self._leak_detection_task: Optional[asyncio.Task] = None

        # Weak references for tracking objects
        self._tracked_objects: WeakValueDictionary = WeakValueDictionary()
        self._cached_objects: WeakSet = WeakSet()

        # Memory pools for object reuse
        self._object_pools: Dict[str, List] = defaultdict(list)
        self._pool_max_sizes = {
            'small_dict': 1000,
            'small_list': 1000,
            'medium_buffer': 100,
            'large_buffer': 10
        }

        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize the memory management system."""
        try:
            # Set initial GC configuration
            self._configure_garbage_collector()

            # Start monitoring tasks
            self._monitoring_task = asyncio.create_task(self._monitor_memory())
            self._optimization_task = asyncio.create_task(self._optimize_memory_periodically())
            self._leak_detection_task = asyncio.create_task(self._detect_memory_leaks())

            # Register built-in optimization callbacks
            self.register_optimization_callback(self._optimize_caches)
            self.register_optimization_callback(self._optimize_object_pools)
            self.register_optimization_callback(self._optimize_weak_references)

            self._initialized = True
            logger.info("Memory management system initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize memory manager: {e}")
            return False

    def _configure_garbage_collector(self):
        """Configure Python garbage collector for optimal performance."""
        # Set GC thresholds for better performance
        # Default is (700, 10, 10) - we make gen0 more frequent, others less frequent
        gc.set_threshold(400, 15, 15)

        # Enable GC debugging in development
        if settings.debug:
            gc.set_debug(gc.DEBUG_STATS)

        logger.info(f"GC thresholds set to: {gc.get_threshold()}")

    async def _monitor_memory(self):
        """Background task to monitor memory usage."""
        while self._initialized:
            try:
                metrics = await self._collect_memory_metrics()
                self._metrics_history.append(metrics)

                # Keep history within limits
                if len(self._metrics_history) > self.max_memory_history:
                    self._metrics_history = self._metrics_history[-self.max_memory_history:]

                # Update Prometheus metrics
                metrics_collector.update_cache_metrics(
                    cache_type="memory",
                    hit_ratio=0.0,  # Not applicable for memory
                    items_count=metrics.gc_objects,
                    memory_usage=metrics.rss_bytes
                )

                # Trigger emergency optimization if needed
                if metrics.pressure_level in [MemoryPressureLevel.HIGH, MemoryPressureLevel.CRITICAL]:
                    logger.warning(f"High memory pressure detected: {metrics.percent_used:.1f}%")
                    asyncio.create_task(self._emergency_memory_optimization())

                # Adaptive monitoring frequency
                if metrics.pressure_level == MemoryPressureLevel.CRITICAL:
                    await asyncio.sleep(5)  # Monitor every 5 seconds
                elif metrics.pressure_level == MemoryPressureLevel.HIGH:
                    await asyncio.sleep(15)  # Monitor every 15 seconds
                else:
                    await asyncio.sleep(30)  # Monitor every 30 seconds

            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                await asyncio.sleep(60)

    async def _collect_memory_metrics(self) -> MemoryMetrics:
        """Collect current memory usage metrics."""
        try:
            # Process memory info
            process = psutil.Process()
            memory_info = process.memory_info()

            # System memory info
            system_memory = psutil.virtual_memory()

            # GC statistics
            gc_stats = gc.get_stats()
            gc_objects = len(gc.get_objects())

            # Calculate memory pressure level
            pressure_level = self._calculate_pressure_level(system_memory.percent)

            # Detect large objects
            large_objects_count = self._count_large_objects()

            return MemoryMetrics(
                rss_bytes=memory_info.rss,
                vms_bytes=memory_info.vms,
                percent_used=system_memory.percent,
                available_bytes=system_memory.available,
                gc_objects=gc_objects,
                gc_collections=[stat['collections'] for stat in gc_stats],
                large_objects_count=large_objects_count,
                pressure_level=pressure_level
            )

        except Exception as e:
            logger.error(f"Failed to collect memory metrics: {e}")
            return MemoryMetrics()

    def _calculate_pressure_level(self, memory_percent: float) -> MemoryPressureLevel:
        """Calculate memory pressure level based on usage percentage."""
        if memory_percent >= self.critical_pressure_threshold:
            return MemoryPressureLevel.CRITICAL
        elif memory_percent >= self.high_pressure_threshold:
            return MemoryPressureLevel.HIGH
        elif memory_percent >= self.moderate_pressure_threshold:
            return MemoryPressureLevel.MODERATE
        else:
            return MemoryPressureLevel.LOW

    def _count_large_objects(self) -> int:
        """Count objects larger than the threshold."""
        large_objects = 0
        threshold_bytes = self.large_object_threshold_mb * 1024 * 1024

        try:
            # This is expensive, so only do it occasionally
            if len(self._metrics_history) % 10 == 0:  # Every 10th check
                for obj in gc.get_objects():
                    try:
                        size = sys.getsizeof(obj)
                        if size > threshold_bytes:
                            large_objects += 1
                    except:
                        continue  # Skip objects that can't be sized

        except Exception as e:
            logger.debug(f"Large object counting failed: {e}")

        return large_objects

    async def _optimize_memory_periodically(self):
        """Background task for periodic memory optimization."""
        while self._initialized:
            try:
                current_metrics = self._metrics_history[-1] if self._metrics_history else MemoryMetrics()

                # Determine optimization frequency based on pressure
                if current_metrics.pressure_level == MemoryPressureLevel.CRITICAL:
                    sleep_time = self.emergency_gc_frequency_seconds
                elif current_metrics.pressure_level == MemoryPressureLevel.HIGH:
                    sleep_time = self.emergency_gc_frequency_seconds * 2
                else:
                    sleep_time = self.gc_frequency_seconds

                # Run optimization
                result = await self.optimize_memory()

                if result.success and result.freed_bytes > 0:
                    logger.info(f"Periodic optimization freed {result.freed_bytes / 1024 / 1024:.1f}MB")

                await asyncio.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Periodic memory optimization error: {e}")
                await asyncio.sleep(self.gc_frequency_seconds)

    async def _detect_memory_leaks(self):
        """Background task to detect potential memory leaks."""
        while self._initialized:
            try:
                # Run leak detection every 5 minutes
                await asyncio.sleep(300)

                if len(self._metrics_history) < 10:
                    continue

                # Analyze memory trend over last 10 measurements
                recent_metrics = self._metrics_history[-10:]
                memory_trend = [m.rss_bytes for m in recent_metrics]

                # Calculate if memory is consistently increasing
                increases = 0
                for i in range(1, len(memory_trend)):
                    if memory_trend[i] > memory_trend[i-1]:
                        increases += 1

                # If memory increased in 80% of measurements, potential leak
                if increases >= 8:
                    leak_rate_mb_per_min = (memory_trend[-1] - memory_trend[0]) / (1024 * 1024 * 5)

                    if leak_rate_mb_per_min > 1.0:  # More than 1MB per minute
                        logger.warning(f"Potential memory leak detected: {leak_rate_mb_per_min:.2f}MB/min")

                        # Run detailed analysis
                        await self._analyze_potential_leak()

            except Exception as e:
                logger.error(f"Memory leak detection error: {e}")
                await asyncio.sleep(300)

    async def _analyze_potential_leak(self):
        """Analyze potential memory leak in detail."""
        try:
            # Take a snapshot of all objects
            all_objects = muppy.get_objects()
            sum_obj = summary.summarize(all_objects)

            # Log top memory consumers
            logger.warning("Top memory consumers during potential leak:")
            for line in summary.format_(sum_obj)[:10]:
                logger.warning(line)

            # Track growth of specific object types
            self._memory_tracker.print_diff()

        except Exception as e:
            logger.error(f"Leak analysis failed: {e}")

    async def _emergency_memory_optimization(self):
        """Emergency memory optimization under high pressure."""
        try:
            logger.warning("Running emergency memory optimization")

            # Force immediate garbage collection
            collected = gc.collect()
            logger.info(f"Emergency GC collected {collected} objects")

            # Run all optimization callbacks
            total_freed = 0
            for callback in self._optimization_callbacks:
                try:
                    freed = await self._run_optimization_callback(callback)
                    total_freed += freed
                except Exception as e:
                    logger.error(f"Optimization callback failed: {e}")

            # Clear object pools if still under pressure
            freed_from_pools = self._clear_object_pools()
            total_freed += freed_from_pools

            logger.info(f"Emergency optimization freed approximately {total_freed / 1024 / 1024:.1f}MB")

        except Exception as e:
            logger.error(f"Emergency memory optimization failed: {e}")

    async def optimize_memory(self) -> MemoryOptimizationResult:
        """Run comprehensive memory optimization."""
        start_time = time.perf_counter()
        initial_memory = psutil.Process().memory_info().rss
        techniques_applied = []

        try:
            # 1. Run garbage collection
            collected_objects = gc.collect()
            techniques_applied.append(f"garbage_collection({collected_objects}_objects)")

            # 2. Run optimization callbacks
            for callback in self._optimization_callbacks:
                try:
                    callback_name = getattr(callback, '__name__', 'unknown')
                    await self._run_optimization_callback(callback)
                    techniques_applied.append(f"callback({callback_name})")
                except Exception as e:
                    logger.error(f"Optimization callback {callback_name} failed: {e}")

            # 3. Optimize object pools
            pool_freed = self._optimize_object_pools()
            if pool_freed > 0:
                techniques_applied.append(f"object_pools({pool_freed}_bytes)")

            # 4. Clear weak references to dead objects
            weak_refs_cleared = self._clear_dead_weak_references()
            if weak_refs_cleared > 0:
                techniques_applied.append(f"weak_refs({weak_refs_cleared}_cleared)")

            # Calculate results
            final_memory = psutil.Process().memory_info().rss
            freed_bytes = max(0, initial_memory - final_memory)
            optimization_time_ms = (time.perf_counter() - start_time) * 1000

            result = MemoryOptimizationResult(
                freed_bytes=freed_bytes,
                objects_collected=collected_objects,
                optimization_time_ms=optimization_time_ms,
                techniques_applied=techniques_applied,
                success=True
            )

            if freed_bytes > 1024 * 1024:  # Only log if freed more than 1MB
                logger.info(f"Memory optimization freed {freed_bytes / 1024 / 1024:.1f}MB in {optimization_time_ms:.1f}ms")

            return result

        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return MemoryOptimizationResult(
                freed_bytes=0,
                objects_collected=0,
                optimization_time_ms=(time.perf_counter() - start_time) * 1000,
                techniques_applied=techniques_applied,
                success=False,
                error_message=str(e)
            )

    async def _run_optimization_callback(self, callback: Callable) -> int:
        """Run an optimization callback and return bytes freed estimate."""
        try:
            if asyncio.iscoroutinefunction(callback):
                result = await callback()
            else:
                result = callback()

            # If callback returns an integer, treat as bytes freed
            if isinstance(result, int):
                return result
            else:
                return 0

        except Exception as e:
            logger.error(f"Optimization callback failed: {e}")
            return 0

    async def _optimize_caches(self) -> int:
        """Optimize application caches."""
        freed_estimate = 0

        try:
            # This would integrate with actual cache managers
            # For now, provide framework for cache optimization
            logger.debug("Running cache optimization")

            # Example optimizations:
            # - Remove expired cache entries
            # - Evict least recently used items
            # - Compress cache values
            # - Clear debugging caches

        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")

        return freed_estimate

    def _optimize_object_pools(self) -> int:
        """Optimize object pools by removing excess objects."""
        freed_estimate = 0

        try:
            for pool_name, pool in self._object_pools.items():
                max_size = self._pool_max_sizes.get(pool_name, 100)

                if len(pool) > max_size:
                    excess_objects = len(pool) - max_size
                    removed_objects = pool[max_size:]

                    # Estimate freed bytes (rough approximation)
                    for obj in removed_objects:
                        try:
                            freed_estimate += sys.getsizeof(obj)
                        except:
                            freed_estimate += 1024  # Default estimate

                    # Clear excess objects
                    pool[:] = pool[:max_size]

                    logger.debug(f"Optimized pool {pool_name}: removed {excess_objects} objects")

        except Exception as e:
            logger.error(f"Object pool optimization failed: {e}")

        return freed_estimate

    async def _optimize_weak_references(self) -> int:
        """Optimize weak reference collections."""
        return self._clear_dead_weak_references()

    def _clear_dead_weak_references(self) -> int:
        """Clear dead weak references."""
        cleared_count = 0

        try:
            # Clear dead references from tracked objects
            dead_keys = [key for key, value in self._tracked_objects.items() if value is None]
            for key in dead_keys:
                try:
                    del self._tracked_objects[key]
                    cleared_count += 1
                except:
                    pass

        except Exception as e:
            logger.error(f"Weak reference clearing failed: {e}")

        return cleared_count

    def _clear_object_pools(self) -> int:
        """Clear all object pools in emergency situations."""
        freed_estimate = 0

        try:
            for pool_name, pool in self._object_pools.items():
                for obj in pool:
                    try:
                        freed_estimate += sys.getsizeof(obj)
                    except:
                        freed_estimate += 1024

                pool.clear()
                logger.debug(f"Emergency cleared pool: {pool_name}")

        except Exception as e:
            logger.error(f"Object pool clearing failed: {e}")

        return freed_estimate

    def register_optimization_callback(self, callback: Callable):
        """Register a callback to be called during memory optimization."""
        self._optimization_callbacks.append(callback)
        logger.info(f"Registered optimization callback: {getattr(callback, '__name__', 'unknown')}")

    def get_object_from_pool(self, pool_name: str, factory: Callable):
        """Get an object from pool or create new one."""
        pool = self._object_pools[pool_name]

        if pool:
            return pool.pop()
        else:
            return factory()

    def return_object_to_pool(self, pool_name: str, obj: Any):
        """Return an object to the pool for reuse."""
        pool = self._object_pools[pool_name]
        max_size = self._pool_max_sizes.get(pool_name, 100)

        if len(pool) < max_size:
            # Reset object state if it has a reset method
            if hasattr(obj, 'reset'):
                obj.reset()
            elif hasattr(obj, 'clear'):
                obj.clear()

            pool.append(obj)

    def track_object(self, key: str, obj: Any):
        """Track an object with weak reference."""
        self._tracked_objects[key] = obj

    def get_memory_status(self) -> Dict[str, Any]:
        """Get current memory status and metrics."""
        current_metrics = self._metrics_history[-1] if self._metrics_history else MemoryMetrics()

        return {
            "current_usage": {
                "rss_mb": current_metrics.rss_bytes / (1024 * 1024),
                "vms_mb": current_metrics.vms_bytes / (1024 * 1024),
                "percent_used": current_metrics.percent_used,
                "pressure_level": current_metrics.pressure_level.value,
                "gc_objects": current_metrics.gc_objects,
                "large_objects": current_metrics.large_objects_count
            },
            "thresholds": {
                "moderate_pressure": self.moderate_pressure_threshold,
                "high_pressure": self.high_pressure_threshold,
                "critical_pressure": self.critical_pressure_threshold
            },
            "optimization": {
                "registered_callbacks": len(self._optimization_callbacks),
                "object_pools": {name: len(pool) for name, pool in self._object_pools.items()},
                "tracked_objects": len(self._tracked_objects),
                "cached_objects": len(self._cached_objects)
            },
            "gc_stats": gc.get_stats(),
            "history_length": len(self._metrics_history)
        }

    def get_memory_trend_analysis(self) -> Dict[str, Any]:
        """Analyze memory usage trends."""
        if len(self._metrics_history) < 10:
            return {"status": "insufficient_data", "message": "Need at least 10 data points"}

        recent_metrics = self._metrics_history[-10:]

        # Calculate trends
        memory_values = [m.rss_bytes for m in recent_metrics]
        gc_object_counts = [m.gc_objects for m in recent_metrics]

        memory_trend = "stable"
        if memory_values[-1] > memory_values[0] * 1.1:
            memory_trend = "increasing"
        elif memory_values[-1] < memory_values[0] * 0.9:
            memory_trend = "decreasing"

        avg_memory_mb = sum(memory_values) / len(memory_values) / (1024 * 1024)
        max_memory_mb = max(memory_values) / (1024 * 1024)

        return {
            "trend": memory_trend,
            "average_memory_mb": avg_memory_mb,
            "peak_memory_mb": max_memory_mb,
            "memory_growth_rate_mb_per_sample": (memory_values[-1] - memory_values[0]) / len(memory_values) / (1024 * 1024),
            "gc_objects_trend": {
                "average": sum(gc_object_counts) / len(gc_object_counts),
                "max": max(gc_object_counts),
                "min": min(gc_object_counts)
            },
            "pressure_distribution": {
                level.value: sum(1 for m in recent_metrics if m.pressure_level == level)
                for level in MemoryPressureLevel
            }
        }

    async def cleanup(self):
        """Clean up memory manager resources."""
        try:
            self._initialized = False

            # Cancel background tasks
            for task in [self._monitoring_task, self._optimization_task, self._leak_detection_task]:
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            # Final cleanup
            self._clear_object_pools()
            self._tracked_objects.clear()
            self._cached_objects.clear()

            logger.info("Memory manager cleaned up successfully")

        except Exception as e:
            logger.error(f"Memory manager cleanup error: {e}")

# Global memory manager instance
memory_manager = MemoryManager()

# Convenience functions
async def initialize_memory_manager() -> bool:
    """Initialize the memory management system."""
    return await memory_manager.initialize()

async def cleanup_memory_manager():
    """Clean up the memory management system."""
    await memory_manager.cleanup()

async def optimize_memory() -> MemoryOptimizationResult:
    """Run memory optimization."""
    return await memory_manager.optimize_memory()

def get_memory_status() -> Dict[str, Any]:
    """Get current memory status."""
    return memory_manager.get_memory_status()

# Decorators for memory optimization
def memory_optimized(pool_name: str = None):
    """Decorator to automatically manage object lifecycle with memory optimization."""
    def decorator(cls):
        original_init = cls.__init__

        def __init__(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            if pool_name:
                memory_manager.track_object(f"{cls.__name__}_{id(self)}", self)

        cls.__init__ = __init__
        return cls

    return decorator

def cached_method(ttl_seconds: int = 300):
    """Decorator to cache method results with automatic cleanup."""
    def decorator(func):
        cache = {}

        async def wrapper(*args, **kwargs):
            key = str(hash(str(args) + str(sorted(kwargs.items()))))
            now = time.time()

            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl_seconds:
                    return result

            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            cache[key] = (result, now)

            # Cleanup old entries periodically
            if len(cache) % 100 == 0:
                expired_keys = [k for k, (_, ts) in cache.items() if now - ts > ttl_seconds]
                for k in expired_keys:
                    del cache[k]

            return result

        return wrapper
    return decorator