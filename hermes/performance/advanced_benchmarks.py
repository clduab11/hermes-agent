"""
Advanced performance benchmarking and load testing suite for HERMES.
"""

import asyncio
import time
import logging
import statistics
import json
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum

import httpx
import websockets
import psutil
import numpy as np
from scipy import stats

from ..config import settings
from ..monitoring.enhanced_metrics import metrics_collector

logger = logging.getLogger(__name__)

class BenchmarkType(Enum):
    """Types of benchmarks available."""
    HTTP_LOAD = "http_load"
    WEBSOCKET_STRESS = "websocket_stress"
    DATABASE_PERFORMANCE = "database_performance"
    CACHE_THROUGHPUT = "cache_throughput"
    VOICE_PIPELINE = "voice_pipeline"
    MEMORY_STRESS = "memory_stress"
    CONCURRENT_USERS = "concurrent_users"
    SYSTEM_LIMITS = "system_limits"

@dataclass
class BenchmarkConfig:
    """Configuration for a benchmark test."""
    name: str
    benchmark_type: BenchmarkType
    duration_seconds: int = 60
    concurrent_users: int = 10
    requests_per_user: int = 100
    ramp_up_seconds: int = 10
    ramp_down_seconds: int = 10
    target_host: str = "http://localhost:8000"
    custom_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BenchmarkResult:
    """Results from a benchmark test."""
    config: BenchmarkConfig
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    bytes_transferred: int
    errors: List[str] = field(default_factory=list)
    system_metrics: Dict[str, Any] = field(default_factory=dict)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage."""
        return 100.0 - self.success_rate

    @property
    def duration_seconds(self) -> float:
        """Calculate actual test duration."""
        return (self.end_time - self.start_time).total_seconds()

class PerformanceBenchmarkSuite:
    """Advanced performance benchmarking suite."""

    def __init__(self):
        self.results_history: List[BenchmarkResult] = []
        self._system_monitor_task: Optional[asyncio.Task] = None
        self._system_metrics: List[Dict[str, Any]] = []
        self._baseline_metrics: Optional[Dict[str, Any]] = None

    def _process_benchmark_results(
        self, 
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process benchmark operation results into standardized metrics.
        
        Args:
            results: List of operation results with 'success', 'response_time', optional 'error', optional 'bytes'
            
        Returns:
            Dict with response_times, errors, successful/failed request counts, bytes_transferred
        """
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0
        bytes_transferred = 0  # Initialize locally to accumulate correctly
        
        for result in results:
            if result.get("success", False):
                successful_requests += 1
                # Accumulate bytes if provided in result
                if "bytes" in result:
                    bytes_transferred += result["bytes"]
            else:
                failed_requests += 1
                if "error" in result:
                    errors.append(result["error"])
            
            if "response_time" in result:
                response_times.append(result["response_time"])
        
        return {
            "response_times": response_times,
            "errors": errors,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "bytes_transferred": bytes_transferred
        }

    async def run_benchmark(self, config: BenchmarkConfig) -> BenchmarkResult:
        """Run a single benchmark test."""
        logger.info(f"Starting benchmark: {config.name}")

        # Start system monitoring
        await self._start_system_monitoring()

        # Capture baseline metrics
        self._baseline_metrics = await self._capture_system_snapshot()

        start_time = datetime.utcnow()
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0
        bytes_transferred = 0

        try:
            # Execute benchmark based on type
            if config.benchmark_type == BenchmarkType.HTTP_LOAD:
                results = await self._run_http_load_test(config)
            elif config.benchmark_type == BenchmarkType.WEBSOCKET_STRESS:
                results = await self._run_websocket_stress_test(config)
            elif config.benchmark_type == BenchmarkType.DATABASE_PERFORMANCE:
                results = await self._run_database_performance_test(config)
            elif config.benchmark_type == BenchmarkType.CACHE_THROUGHPUT:
                results = await self._run_cache_throughput_test(config)
            elif config.benchmark_type == BenchmarkType.VOICE_PIPELINE:
                results = await self._run_voice_pipeline_test(config)
            elif config.benchmark_type == BenchmarkType.MEMORY_STRESS:
                results = await self._run_memory_stress_test(config)
            elif config.benchmark_type == BenchmarkType.CONCURRENT_USERS:
                results = await self._run_concurrent_users_test(config)
            elif config.benchmark_type == BenchmarkType.SYSTEM_LIMITS:
                results = await self._run_system_limits_test(config)
            else:
                raise ValueError(f"Unknown benchmark type: {config.benchmark_type}")

            # Extract results
            response_times = results.get("response_times", [])
            errors = results.get("errors", [])
            successful_requests = results.get("successful_requests", 0)
            failed_requests = results.get("failed_requests", 0)
            bytes_transferred = results.get("bytes_transferred", 0)

        except Exception as e:
            logger.error(f"Benchmark execution failed: {e}")
            errors.append(str(e))
            failed_requests = config.requests_per_user * config.concurrent_users

        finally:
            end_time = datetime.utcnow()
            await self._stop_system_monitoring()

        # Calculate statistics
        total_requests = successful_requests + failed_requests
        duration = (end_time - start_time).total_seconds()

        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p50_response_time = statistics.median(response_times)
            p95_response_time = np.percentile(response_times, 95)
            p99_response_time = np.percentile(response_times, 99)
        else:
            avg_response_time = min_response_time = max_response_time = 0.0
            p50_response_time = p95_response_time = p99_response_time = 0.0

        requests_per_second = successful_requests / duration if duration > 0 else 0

        # Capture final system metrics
        final_metrics = await self._capture_system_snapshot()
        system_metrics = self._calculate_system_delta(self._baseline_metrics, final_metrics)

        # Create result
        result = BenchmarkResult(
            config=config,
            start_time=start_time,
            end_time=end_time,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p50_response_time=p50_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            bytes_transferred=bytes_transferred,
            errors=errors[:100],  # Keep only first 100 errors
            system_metrics=system_metrics
        )

        self.results_history.append(result)
        logger.info(f"Benchmark completed: {config.name} - {result.success_rate:.1f}% success")

        return result

    async def _run_http_load_test(self, config: BenchmarkConfig) -> Dict[str, Any]:
        """Run HTTP load test."""
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0
        bytes_transferred = 0

        async def make_request(session: httpx.AsyncClient, url: str) -> Dict[str, Any]:
            """Make a single HTTP request."""
            start_time = time.perf_counter()
            try:
                response = await session.get(url, timeout=30.0)
                end_time = time.perf_counter()

                return {
                    "success": True,
                    "response_time": end_time - start_time,
                    "status_code": response.status_code,
                    "bytes": len(response.content)
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "response_time": time.perf_counter() - start_time
                }

        async def user_session(user_id: int):
            """Simulate a user session."""
            nonlocal successful_requests, failed_requests, bytes_transferred

            async with httpx.AsyncClient() as session:
                user_response_times = []
                user_errors = []

                # Ramp-up delay
                await asyncio.sleep(user_id * (config.ramp_up_seconds / config.concurrent_users))

                # Execute requests
                for _ in range(config.requests_per_user):
                    result = await make_request(session, f"{config.target_host}/health")

                    if result["success"]:
                        successful_requests += 1
                        bytes_transferred += result.get("bytes", 0)
                    else:
                        failed_requests += 1
                        user_errors.append(result["error"])

                    user_response_times.append(result["response_time"])

                    # Small delay between requests
                    await asyncio.sleep(0.01)

                return user_response_times, user_errors

        # Run concurrent user sessions
        tasks = [user_session(i) for i in range(config.concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
                failed_requests += config.requests_per_user
            else:
                user_response_times, user_errors = result
                response_times.extend(user_response_times)
                errors.extend(user_errors)

        return {
            "response_times": response_times,
            "errors": errors,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "bytes_transferred": bytes_transferred
        }

    async def _run_websocket_stress_test(self, config: BenchmarkConfig) -> Dict[str, Any]:
        """Run WebSocket stress test."""
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0

        async def websocket_session(user_id: int):
            """Simulate a WebSocket session."""
            nonlocal successful_requests, failed_requests

            try:
                uri = config.target_host.replace("http", "ws") + "/ws/voice"

                async with websockets.connect(uri) as websocket:
                    session_response_times = []

                    # Send messages
                    for i in range(config.requests_per_user):
                        start_time = time.perf_counter()

                        try:
                            # Send test message
                            test_message = {
                                "type": "audio_data",
                                "data": "base64_encoded_audio_data",
                                "session_id": f"test_session_{user_id}_{i}"
                            }

                            await websocket.send(json.dumps(test_message))

                            # Wait for response
                            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            end_time = time.perf_counter()

                            successful_requests += 1
                            session_response_times.append(end_time - start_time)

                        except asyncio.TimeoutError:
                            failed_requests += 1
                            errors.append("WebSocket response timeout")

                        except Exception as e:
                            failed_requests += 1
                            errors.append(f"WebSocket error: {e}")

                    return session_response_times

            except Exception as e:
                errors.append(f"WebSocket connection error: {e}")
                failed_requests += config.requests_per_user
                return []

        # Run concurrent WebSocket sessions
        tasks = [websocket_session(i) for i in range(config.concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
            else:
                response_times.extend(result)

        return {
            "response_times": response_times,
            "errors": errors,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "bytes_transferred": 0
        }

    async def _run_database_performance_test(self, config: BenchmarkConfig) -> Dict[str, Any]:
        """Run database performance test."""
        # This would integrate with the actual database manager
        # For now, simulate database operations

        async def simulate_db_operation():
            """Simulate a database operation."""
            start_time = time.perf_counter()

            try:
                # Simulate database query time
                await asyncio.sleep(0.001 + np.random.exponential(0.01))
                end_time = time.perf_counter()

                return {
                    "success": True,
                    "response_time": end_time - start_time
                }

            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "response_time": time.perf_counter() - start_time
                }

        # Run concurrent database operations
        total_operations = config.concurrent_users * config.requests_per_user
        tasks = [simulate_db_operation() for _ in range(total_operations)]
        results = await asyncio.gather(*tasks)

        # Process results using helper method
        return self._process_benchmark_results(results)

    async def _run_cache_throughput_test(self, config: BenchmarkConfig) -> Dict[str, Any]:
        """Run cache throughput test."""
        # This would integrate with the actual cache manager
        # For now, simulate cache operations

        response_times = []
        successful_requests = 0
        failed_requests = 0

        async def cache_operations():
            """Perform cache operations."""
            for _ in range(config.requests_per_user):
                start_time = time.perf_counter()

                # Simulate cache get/set operations
                await asyncio.sleep(0.0001)  # Very fast cache operation

                end_time = time.perf_counter()
                response_times.append(end_time - start_time)
                successful_requests += 1

        tasks = [cache_operations() for _ in range(config.concurrent_users)]
        await asyncio.gather(*tasks)

        return {
            "response_times": response_times,
            "errors": [],
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "bytes_transferred": 0
        }

    async def _run_voice_pipeline_test(self, config: BenchmarkConfig) -> Dict[str, Any]:
        """Run voice pipeline performance test."""
        # Simulate voice processing pipeline

        async def process_voice_sample():
            """Simulate voice processing."""
            start_time = time.perf_counter()

            try:
                # Simulate voice processing stages
                await asyncio.sleep(0.1)  # STT processing
                await asyncio.sleep(0.05)  # NLP processing
                await asyncio.sleep(0.08)  # TTS processing

                end_time = time.perf_counter()
                return {
                    "success": True,
                    "response_time": end_time - start_time
                }

            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "response_time": time.perf_counter() - start_time
                }

        # Run concurrent voice processing
        total_samples = config.concurrent_users * config.requests_per_user
        tasks = [process_voice_sample() for _ in range(total_samples)]
        results = await asyncio.gather(*tasks)

        # Process results using helper method
        return self._process_benchmark_results(results)

    async def _run_memory_stress_test(self, config: BenchmarkConfig) -> Dict[str, Any]:
        """Run memory stress test."""
        async def memory_intensive_task():
            """Perform memory-intensive operations."""
            start_time = time.perf_counter()

            try:
                # Allocate and manipulate memory
                data = []
                for _ in range(10000):
                    data.append("x" * 1000)

                # Process the data
                processed = [item.upper() for item in data[:5000]]
                del data
                del processed

                end_time = time.perf_counter()
                return {
                    "success": True,
                    "response_time": end_time - start_time
                }

            except MemoryError as e:
                return {
                    "success": False,
                    "error": f"Memory error: {e}",
                    "response_time": time.perf_counter() - start_time
                }

        # Run memory stress operations
        total_operations = config.concurrent_users * config.requests_per_user
        tasks = [memory_intensive_task() for _ in range(total_operations)]
        results = await asyncio.gather(*tasks)

        # Process results using helper method
        return self._process_benchmark_results(results)

    async def _run_concurrent_users_test(self, config: BenchmarkConfig) -> Dict[str, Any]:
        """Run concurrent users simulation test."""
        # This combines multiple types of operations to simulate real user behavior
        response_times = []
        successful_requests = 0
        failed_requests = 0
        errors = []

        async def simulate_user_behavior(user_id: int):
            """Simulate realistic user behavior."""
            user_response_times = []

            try:
                async with httpx.AsyncClient() as session:
                    # User login
                    start_time = time.perf_counter()
                    response = await session.post(f"{config.target_host}/auth/token", json={
                        "subject": f"test_user_{user_id}",
                        "tenant_id": "test_tenant"
                    })
                    end_time = time.perf_counter()

                    if response.status_code in [200, 201]:
                        successful_requests += 1
                        user_response_times.append(end_time - start_time)
                    else:
                        failed_requests += 1
                        errors.append(f"Login failed: {response.status_code}")

                    # Multiple API calls
                    endpoints = ["/health", "/status", "/voices"]
                    for endpoint in endpoints:
                        start_time = time.perf_counter()
                        response = await session.get(f"{config.target_host}{endpoint}")
                        end_time = time.perf_counter()

                        if response.status_code == 200:
                            successful_requests += 1
                        else:
                            failed_requests += 1
                            errors.append(f"{endpoint} failed: {response.status_code}")

                        user_response_times.append(end_time - start_time)
                        await asyncio.sleep(0.1)  # Think time

            except Exception as e:
                failed_requests += len(endpoints) + 1
                errors.append(f"User {user_id} session failed: {e}")

            return user_response_times

        # Run concurrent user simulations
        tasks = [simulate_user_behavior(i) for i in range(config.concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
            else:
                response_times.extend(result)

        return {
            "response_times": response_times,
            "errors": errors,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "bytes_transferred": 0
        }

    async def _run_system_limits_test(self, config: BenchmarkConfig) -> Dict[str, Any]:
        """Run system limits test to find breaking points."""
        response_times = []
        successful_requests = 0
        failed_requests = 0
        errors = []

        # Gradually increase load until system breaks
        max_concurrent = config.concurrent_users
        step_size = max(1, max_concurrent // 10)

        for concurrent_level in range(step_size, max_concurrent + 1, step_size):
            logger.info(f"Testing with {concurrent_level} concurrent operations")

            async def stress_operation():
                """Single stress operation."""
                start_time = time.perf_counter()

                try:
                    # Mix of CPU and I/O intensive operations
                    await asyncio.sleep(0.001)  # I/O simulation

                    # CPU intensive work
                    result = sum(i ** 2 for i in range(1000))

                    end_time = time.perf_counter()
                    return {
                        "success": True,
                        "response_time": end_time - start_time
                    }

                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "response_time": time.perf_counter() - start_time
                    }

            # Run stress operations at current concurrency level
            tasks = [stress_operation() for _ in range(concurrent_level)]
            level_results = await asyncio.gather(*tasks)

            # Process results for this level
            level_success = 0
            level_failed = 0

            for result in level_results:
                if result["success"]:
                    level_success += 1
                    successful_requests += 1
                else:
                    level_failed += 1
                    failed_requests += 1
                    errors.append(result["error"])

                response_times.append(result["response_time"])

            # Check if system is breaking down
            failure_rate = level_failed / len(level_results) if level_results else 0
            avg_response_time = statistics.mean([r["response_time"] for r in level_results])

            if failure_rate > 0.1 or avg_response_time > 5.0:  # 10% failure or 5s response time
                logger.warning(f"System limits reached at {concurrent_level} concurrent operations")
                break

            await asyncio.sleep(1)  # Cool down between levels

        return {
            "response_times": response_times,
            "errors": errors,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "bytes_transferred": 0
        }

    async def _start_system_monitoring(self):
        """Start monitoring system metrics during benchmark."""
        self._system_metrics = []

        async def monitor():
            while True:
                try:
                    metrics = await self._capture_system_snapshot()
                    self._system_metrics.append(metrics)
                    await asyncio.sleep(1)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"System monitoring error: {e}")

        self._system_monitor_task = asyncio.create_task(monitor())

    async def _stop_system_monitoring(self):
        """Stop system monitoring."""
        if self._system_monitor_task:
            self._system_monitor_task.cancel()
            try:
                await self._system_monitor_task
            except asyncio.CancelledError:
                pass

    async def _capture_system_snapshot(self) -> Dict[str, Any]:
        """Capture current system metrics snapshot."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()

            # Memory metrics
            memory = psutil.virtual_memory()

            # Disk metrics
            disk = psutil.disk_usage('/')

            # Network metrics
            network = psutil.net_io_counters()

            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "process": {
                    "memory_rss": process_memory.rss,
                    "memory_vms": process_memory.vms
                }
            }

        except Exception as e:
            logger.error(f"Failed to capture system snapshot: {e}")
            return {}

    def _calculate_system_delta(self, baseline: Optional[Dict], final: Dict) -> Dict[str, Any]:
        """Calculate the delta between baseline and final system metrics."""
        if not baseline:
            return final

        try:
            return {
                "cpu_max_percent": max(
                    [m.get("cpu", {}).get("percent", 0) for m in self._system_metrics]
                ),
                "memory_peak_used": max(
                    [m.get("memory", {}).get("used", 0) for m in self._system_metrics]
                ),
                "network_bytes_delta": {
                    "sent": final.get("network", {}).get("bytes_sent", 0) - baseline.get("network", {}).get("bytes_sent", 0),
                    "recv": final.get("network", {}).get("bytes_recv", 0) - baseline.get("network", {}).get("bytes_recv", 0)
                },
                "process_memory_delta": {
                    "rss": final.get("process", {}).get("memory_rss", 0) - baseline.get("process", {}).get("memory_rss", 0)
                }
            }

        except Exception as e:
            logger.error(f"Failed to calculate system delta: {e}")
            return {}

    def generate_performance_report(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        if not results:
            return {"error": "No benchmark results available"}

        # Aggregate statistics
        total_requests = sum(r.total_requests for r in results)
        total_successful = sum(r.successful_requests for r in results)
        total_failed = sum(r.failed_requests for r in results)

        avg_success_rate = statistics.mean([r.success_rate for r in results])
        avg_response_time = statistics.mean([r.avg_response_time for r in results])
        max_rps = max([r.requests_per_second for r in results])

        # Performance trends
        chronological_results = sorted(results, key=lambda r: r.start_time)
        response_time_trend = [r.avg_response_time for r in chronological_results]
        rps_trend = [r.requests_per_second for r in chronological_results]

        # Statistical analysis
        response_time_stats = {
            "mean": statistics.mean([r.avg_response_time for r in results]),
            "median": statistics.median([r.avg_response_time for r in results]),
            "stdev": statistics.stdev([r.avg_response_time for r in results]) if len(results) > 1 else 0
        }

        return {
            "summary": {
                "total_benchmarks": len(results),
                "total_requests": total_requests,
                "successful_requests": total_successful,
                "failed_requests": total_failed,
                "overall_success_rate": (total_successful / total_requests * 100) if total_requests > 0 else 0,
                "avg_response_time": avg_response_time,
                "max_requests_per_second": max_rps
            },
            "performance_analysis": {
                "response_time_stats": response_time_stats,
                "performance_trends": {
                    "response_time_trend": response_time_trend,
                    "rps_trend": rps_trend
                },
                "bottlenecks": self._identify_bottlenecks(results),
                "recommendations": self._generate_recommendations(results)
            },
            "detailed_results": [
                {
                    "name": r.config.name,
                    "type": r.config.benchmark_type.value,
                    "success_rate": r.success_rate,
                    "avg_response_time": r.avg_response_time,
                    "p95_response_time": r.p95_response_time,
                    "requests_per_second": r.requests_per_second,
                    "duration": r.duration_seconds,
                    "errors": len(r.errors)
                }
                for r in results
            ]
        }

    def _identify_bottlenecks(self, results: List[BenchmarkResult]) -> List[str]:
        """Identify performance bottlenecks from benchmark results."""
        bottlenecks = []

        # High response time bottleneck
        high_response_times = [r for r in results if r.avg_response_time > 1.0]
        if high_response_times:
            bottlenecks.append(f"High response times detected in {len(high_response_times)} benchmarks")

        # Low success rate bottleneck
        low_success_rates = [r for r in results if r.success_rate < 95.0]
        if low_success_rates:
            bottlenecks.append(f"Low success rates detected in {len(low_success_rates)} benchmarks")

        # System resource bottlenecks
        cpu_intensive = [r for r in results if r.system_metrics.get("cpu_max_percent", 0) > 80]
        if cpu_intensive:
            bottlenecks.append(f"High CPU usage detected in {len(cpu_intensive)} benchmarks")

        memory_intensive = [r for r in results if r.system_metrics.get("memory_peak_used", 0) > 0.8 * psutil.virtual_memory().total]
        if memory_intensive:
            bottlenecks.append(f"High memory usage detected in {len(memory_intensive)} benchmarks")

        return bottlenecks

    def _generate_recommendations(self, results: List[BenchmarkResult]) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        # Response time recommendations
        avg_response_time = statistics.mean([r.avg_response_time for r in results])
        if avg_response_time > 0.5:
            recommendations.append("Consider optimizing application code to reduce response times")

        if avg_response_time > 1.0:
            recommendations.append("Implement caching to improve response times")

        # Success rate recommendations
        avg_success_rate = statistics.mean([r.success_rate for r in results])
        if avg_success_rate < 99:
            recommendations.append("Investigate and fix error sources to improve reliability")

        # Scaling recommendations
        max_rps = max([r.requests_per_second for r in results]) if results else 0
        if max_rps < 100:
            recommendations.append("Consider horizontal scaling to improve throughput")

        # Resource recommendations
        high_cpu_results = [r for r in results if r.system_metrics.get("cpu_max_percent", 0) > 70]
        if high_cpu_results:
            recommendations.append("Optimize CPU-intensive operations or scale CPU resources")

        return recommendations

# Global benchmark suite instance
benchmark_suite = PerformanceBenchmarkSuite()

# Convenience functions
async def run_comprehensive_benchmarks(target_host: str = "http://localhost:8000") -> Dict[str, Any]:
    """Run a comprehensive suite of benchmarks."""
    configs = [
        BenchmarkConfig("HTTP Load Test", BenchmarkType.HTTP_LOAD, target_host=target_host),
        BenchmarkConfig("WebSocket Stress", BenchmarkType.WEBSOCKET_STRESS, target_host=target_host),
        BenchmarkConfig("Database Performance", BenchmarkType.DATABASE_PERFORMANCE),
        BenchmarkConfig("Cache Throughput", BenchmarkType.CACHE_THROUGHPUT),
        BenchmarkConfig("Voice Pipeline", BenchmarkType.VOICE_PIPELINE),
        BenchmarkConfig("Memory Stress", BenchmarkType.MEMORY_STRESS, concurrent_users=5),
        BenchmarkConfig("Concurrent Users", BenchmarkType.CONCURRENT_USERS, target_host=target_host),
        BenchmarkConfig("System Limits", BenchmarkType.SYSTEM_LIMITS, concurrent_users=50)
    ]

    results = []
    for config in configs:
        try:
            result = await benchmark_suite.run_benchmark(config)
            results.append(result)
        except Exception as e:
            logger.error(f"Benchmark {config.name} failed: {e}")

    return benchmark_suite.generate_performance_report(results)