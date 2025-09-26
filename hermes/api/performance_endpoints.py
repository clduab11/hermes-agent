"""
Performance monitoring and optimization API endpoints for HERMES.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..performance.performance_suite import performance_suite
from ..performance.advanced_benchmarks import BenchmarkConfig, BenchmarkType
from ..auth.middleware import require_admin_role
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/performance", tags=["Performance"])

# Request/Response models
class OptimizationRequest(BaseModel):
    """Request model for performance optimization."""
    components: Optional[list] = None
    force: bool = False

class BenchmarkRequest(BaseModel):
    """Request model for performance benchmarking."""
    benchmark_type: str
    duration_seconds: int = 60
    concurrent_users: int = 10
    requests_per_user: int = 100

@router.get("/status")
async def get_performance_status() -> Dict[str, Any]:
    """Get comprehensive performance status of the system."""
    try:
        if not performance_suite.status.initialized:
            return {
                "error": "Performance suite not initialized",
                "status": "unavailable"
            }

        status = await performance_suite.get_comprehensive_status()
        return status

    except Exception as e:
        logger.error(f"Failed to get performance status: {e}")
        raise HTTPException(status_code=500, detail=f"Performance status error: {str(e)}")

@router.get("/metrics")
async def get_performance_metrics(
    component: Optional[str] = Query(None, description="Specific component to get metrics for")
) -> Dict[str, Any]:
    """Get detailed performance metrics."""
    try:
        from ..database.optimized_connection import optimized_db_manager
        from ..cache.tenant_cache_manager import tenant_cache_manager
        from ..optimization.memory_manager import memory_manager
        from ..scaling.auto_scaler import auto_scaler

        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "suite_score": performance_suite.status.performance_score
        }

        # Get component-specific metrics
        if not component or component == "database":
            if optimized_db_manager._initialized:
                metrics["database"] = await optimized_db_manager.get_performance_metrics()

        if not component or component == "cache":
            if tenant_cache_manager._initialized:
                metrics["cache"] = await tenant_cache_manager.get_metrics()

        if not component or component == "memory":
            if memory_manager._initialized:
                metrics["memory"] = memory_manager.get_memory_status()

        if not component or component == "scaling":
            if auto_scaler._initialized:
                metrics["scaling"] = await auto_scaler.get_scaling_status()

        return metrics

    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics error: {str(e)}")

@router.post("/optimize")
async def optimize_performance(
    request: OptimizationRequest = OptimizationRequest(),
    _auth = Depends(require_admin_role)
) -> Dict[str, Any]:
    """Run performance optimization across specified components."""
    try:
        if not performance_suite.status.initialized:
            raise HTTPException(
                status_code=503,
                detail="Performance suite not initialized"
            )

        logger.info(f"Running performance optimization: {request}")

        # Run full optimization
        result = await performance_suite.run_full_optimization()

        return {
            "optimization_completed": True,
            "timestamp": datetime.utcnow().isoformat(),
            **result
        }

    except Exception as e:
        logger.error(f"Performance optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization error: {str(e)}")

@router.post("/benchmark")
async def run_performance_benchmark(
    request: BenchmarkRequest,
    _auth = Depends(require_admin_role)
) -> Dict[str, Any]:
    """Run performance benchmarks."""
    try:
        # Only allow benchmarks in development/demo mode
        if not (settings.debug or settings.demo_mode):
            raise HTTPException(
                status_code=403,
                detail="Benchmarks are disabled in production environment"
            )

        # Validate benchmark type
        try:
            benchmark_type = BenchmarkType(request.benchmark_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid benchmark type: {request.benchmark_type}"
            )

        from ..performance.advanced_benchmarks import benchmark_suite

        # Create benchmark configuration
        config = BenchmarkConfig(
            name=f"API Benchmark - {request.benchmark_type}",
            benchmark_type=benchmark_type,
            duration_seconds=request.duration_seconds,
            concurrent_users=request.concurrent_users,
            requests_per_user=request.requests_per_user
        )

        logger.info(f"Running benchmark: {config.name}")

        # Run benchmark
        result = await benchmark_suite.run_benchmark(config)

        return {
            "benchmark_completed": True,
            "config": {
                "name": config.name,
                "type": config.benchmark_type.value,
                "duration": config.duration_seconds,
                "concurrent_users": config.concurrent_users,
                "requests_per_user": config.requests_per_user
            },
            "results": {
                "success_rate": result.success_rate,
                "avg_response_time": result.avg_response_time,
                "requests_per_second": result.requests_per_second,
                "total_requests": result.total_requests,
                "p95_response_time": result.p95_response_time,
                "p99_response_time": result.p99_response_time,
                "errors": len(result.errors),
                "system_metrics": result.system_metrics
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Performance benchmark failed: {e}")
        raise HTTPException(status_code=500, detail=f"Benchmark error: {str(e)}")

@router.get("/benchmarks/comprehensive")
async def run_comprehensive_benchmarks(
    _auth = Depends(require_admin_role)
) -> Dict[str, Any]:
    """Run the full comprehensive benchmark suite."""
    try:
        if not (settings.debug or settings.demo_mode):
            raise HTTPException(
                status_code=403,
                detail="Comprehensive benchmarks are disabled in production"
            )

        result = await performance_suite.run_performance_benchmarks()
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Comprehensive benchmarks failed: {e}")
        raise HTTPException(status_code=500, detail=f"Benchmarks error: {str(e)}")

@router.get("/database/metrics")
async def get_database_metrics(
    tenant_id: Optional[str] = Query(None, description="Specific tenant ID")
) -> Dict[str, Any]:
    """Get detailed database performance metrics."""
    try:
        from ..database.optimized_connection import optimized_db_manager

        if not optimized_db_manager._initialized:
            raise HTTPException(status_code=503, detail="Database manager not initialized")

        if tenant_id:
            # Get tenant-specific metrics
            tenant_metrics = await optimized_db_manager.get_tenant_performance_metrics(tenant_id)
            if not tenant_metrics:
                raise HTTPException(status_code=404, detail="Tenant metrics not found")

            return {
                "tenant_id": tenant_id,
                "metrics": {
                    "total_queries": tenant_metrics.total_queries,
                    "avg_response_time_ms": tenant_metrics.avg_response_time_ms,
                    "cache_hit_ratio": tenant_metrics.cache_hit_ratio,
                    "active_sessions": tenant_metrics.active_sessions,
                    "last_activity": tenant_metrics.last_activity.isoformat()
                }
            }
        else:
            # Get system-wide metrics
            metrics = await optimized_db_manager.get_performance_metrics()
            return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database metrics error: {e}")
        raise HTTPException(status_code=500, detail=f"Database metrics error: {str(e)}")

@router.get("/cache/metrics")
async def get_cache_metrics() -> Dict[str, Any]:
    """Get detailed cache performance metrics."""
    try:
        from ..cache.tenant_cache_manager import tenant_cache_manager

        if not tenant_cache_manager._initialized:
            raise HTTPException(status_code=503, detail="Cache manager not initialized")

        metrics = await tenant_cache_manager.get_metrics()
        return metrics

    except Exception as e:
        logger.error(f"Cache metrics error: {e}")
        raise HTTPException(status_code=500, detail=f"Cache metrics error: {str(e)}")

@router.post("/cache/invalidate")
async def invalidate_cache(
    tenant_id: Optional[str] = Query(None, description="Tenant ID to invalidate cache for"),
    _auth = Depends(require_admin_role)
) -> Dict[str, Any]:
    """Invalidate cache entries."""
    try:
        from ..cache.tenant_cache_manager import tenant_cache_manager

        if not tenant_cache_manager._initialized:
            raise HTTPException(status_code=503, detail="Cache manager not initialized")

        if tenant_id:
            invalidated_count = await tenant_cache_manager.invalidate_tenant(tenant_id)
            return {
                "invalidated": True,
                "tenant_id": tenant_id,
                "entries_removed": invalidated_count
            }
        else:
            # This would invalidate all cache entries - implement if needed
            raise HTTPException(status_code=400, detail="Global cache invalidation not supported")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")
        raise HTTPException(status_code=500, detail=f"Cache invalidation error: {str(e)}")

@router.get("/memory/status")
async def get_memory_status() -> Dict[str, Any]:
    """Get detailed memory usage and optimization status."""
    try:
        from ..optimization.memory_manager import memory_manager

        if not memory_manager._initialized:
            raise HTTPException(status_code=503, detail="Memory manager not initialized")

        status = memory_manager.get_memory_status()
        trend_analysis = memory_manager.get_memory_trend_analysis()

        return {
            "status": status,
            "trend_analysis": trend_analysis
        }

    except Exception as e:
        logger.error(f"Memory status error: {e}")
        raise HTTPException(status_code=500, detail=f"Memory status error: {str(e)}")

@router.post("/memory/optimize")
async def optimize_memory(
    _auth = Depends(require_admin_role)
) -> Dict[str, Any]:
    """Run memory optimization."""
    try:
        from ..optimization.memory_manager import memory_manager

        if not memory_manager._initialized:
            raise HTTPException(status_code=503, detail="Memory manager not initialized")

        result = await memory_manager.optimize_memory()

        return {
            "optimization_completed": True,
            "freed_mb": result.freed_bytes / (1024 * 1024),
            "objects_collected": result.objects_collected,
            "optimization_time_ms": result.optimization_time_ms,
            "techniques_applied": result.techniques_applied,
            "success": result.success,
            "error_message": result.error_message
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Memory optimization error: {e}")
        raise HTTPException(status_code=500, detail=f"Memory optimization error: {str(e)}")

@router.get("/scaling/status")
async def get_scaling_status() -> Dict[str, Any]:
    """Get auto-scaling system status."""
    try:
        from ..scaling.auto_scaler import auto_scaler

        if not auto_scaler._initialized:
            raise HTTPException(status_code=503, detail="Auto-scaler not initialized")

        status = await auto_scaler.get_scaling_status()
        return status

    except Exception as e:
        logger.error(f"Scaling status error: {e}")
        raise HTTPException(status_code=500, detail=f"Scaling status error: {str(e)}")

@router.post("/scaling/rule")
async def update_scaling_rule(
    rule_name: str,
    scale_up_threshold: Optional[float] = None,
    scale_down_threshold: Optional[float] = None,
    enabled: Optional[bool] = None,
    _auth = Depends(require_admin_role)
) -> Dict[str, Any]:
    """Update auto-scaling rule configuration."""
    try:
        from ..scaling.auto_scaler import auto_scaler

        if not auto_scaler._initialized:
            raise HTTPException(status_code=503, detail="Auto-scaler not initialized")

        update_params = {}
        if scale_up_threshold is not None:
            update_params["scale_up_threshold"] = scale_up_threshold
        if scale_down_threshold is not None:
            update_params["scale_down_threshold"] = scale_down_threshold
        if enabled is not None:
            update_params["enabled"] = enabled

        if not update_params:
            raise HTTPException(status_code=400, detail="No parameters provided for update")

        success = await auto_scaler.update_scaling_rule(rule_name, **update_params)

        if not success:
            raise HTTPException(status_code=404, detail=f"Scaling rule '{rule_name}' not found")

        return {
            "rule_updated": True,
            "rule_name": rule_name,
            "updated_parameters": update_params
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scaling rule update error: {e}")
        raise HTTPException(status_code=500, detail=f"Scaling rule update error: {str(e)}")

@router.get("/tenants/{tenant_id}/status")
async def get_tenant_performance_status(tenant_id: str) -> Dict[str, Any]:
    """Get performance status for a specific tenant."""
    try:
        from ..tenancy.isolation_manager import tenant_isolation_manager

        if not tenant_isolation_manager._initialized:
            raise HTTPException(status_code=503, detail="Tenant isolation manager not initialized")

        status = tenant_isolation_manager.get_tenant_status(tenant_id)

        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tenant performance status error: {e}")
        raise HTTPException(status_code=500, detail=f"Tenant status error: {str(e)}")

@router.get("/tenants/overview")
async def get_tenants_overview() -> Dict[str, Any]:
    """Get performance overview for all tenants."""
    try:
        from ..tenancy.isolation_manager import tenant_isolation_manager

        if not tenant_isolation_manager._initialized:
            raise HTTPException(status_code=503, detail="Tenant isolation manager not initialized")

        overview = tenant_isolation_manager.get_all_tenants_status()
        return overview

    except Exception as e:
        logger.error(f"Tenants overview error: {e}")
        raise HTTPException(status_code=500, detail=f"Tenants overview error: {str(e)}")

@router.get("/health")
async def get_performance_health() -> Dict[str, Any]:
    """Get health status of all performance components."""
    try:
        if not performance_suite.status.initialized:
            raise HTTPException(status_code=503, detail="Performance suite not initialized")

        # Get health status from all components
        health_checks = {}

        from ..database.optimized_connection import optimized_db_manager
        from ..cache.tenant_cache_manager import tenant_cache_manager

        if optimized_db_manager._initialized:
            health_checks["database"] = await optimized_db_manager.health_check()

        if tenant_cache_manager._initialized:
            health_checks["cache"] = await tenant_cache_manager.health_check()

        # Overall health determination
        overall_health = "healthy"
        for component, health in health_checks.items():
            if health.get("overall") != "healthy":
                overall_health = "degraded"
                break

        return {
            "overall_health": overall_health,
            "performance_score": performance_suite.status.performance_score,
            "components": health_checks,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Performance health check error: {e}")
        raise HTTPException(status_code=500, detail=f"Health check error: {str(e)}")

@router.get("/recommendations")
async def get_performance_recommendations() -> Dict[str, Any]:
    """Get performance improvement recommendations."""
    try:
        if not performance_suite.status.initialized:
            raise HTTPException(status_code=503, detail="Performance suite not initialized")

        status = await performance_suite.get_comprehensive_status()
        recommendations = status.get("recommendations", [])

        return {
            "recommendations": recommendations,
            "performance_score": performance_suite.status.performance_score,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Performance recommendations error: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendations error: {str(e)}")

# WebSocket endpoint for real-time performance monitoring
@router.websocket("/ws/monitor")
async def performance_monitor_websocket(websocket):
    """WebSocket endpoint for real-time performance monitoring."""
    await websocket.accept()

    try:
        # Send initial status
        initial_status = await performance_suite.get_comprehensive_status()
        await websocket.send_json({
            "type": "initial_status",
            "data": initial_status,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Send periodic updates
        while True:
            await asyncio.sleep(5)  # Update every 5 seconds

            try:
                # Get current performance metrics
                metrics = {
                    "performance_score": performance_suite.status.performance_score,
                    "component_status": performance_suite.status.components_status,
                    "timestamp": datetime.utcnow().isoformat()
                }

                # Add basic system metrics
                import psutil
                metrics["system"] = {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage('/').percent if psutil.disk_usage('/') else 0
                }

                await websocket.send_json({
                    "type": "performance_update",
                    "data": metrics,
                    "timestamp": datetime.utcnow().isoformat()
                })

            except Exception as e:
                logger.error(f"WebSocket update error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })

    except Exception as e:
        logger.error(f"Performance monitoring WebSocket error: {e}")
        await websocket.close()