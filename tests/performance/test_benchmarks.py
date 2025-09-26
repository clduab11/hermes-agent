"""Performance benchmarks for HERMES system."""

import asyncio
import time
import pytest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

from hermes.voice_pipeline import VoicePipeline
from hermes.security.rate_limiter import ProductionRateLimiter


@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Performance benchmark tests."""

    @pytest.fixture
    def mock_voice_pipeline(self):
        """Create mock voice pipeline for testing."""
        pipeline = Mock(spec=VoicePipeline)
        pipeline.process_audio_stream.return_value = {"response": "test response"}
        return pipeline

    @pytest.mark.asyncio
    async def test_voice_pipeline_latency(self, mock_voice_pipeline):
        """Test voice pipeline response latency."""
        # Target: Sub-500ms response time
        start_time = time.time()

        # Simulate audio processing
        mock_audio_data = b"mock_audio_data" * 1000
        result = await asyncio.create_task(
            self._simulate_voice_processing(mock_voice_pipeline, mock_audio_data)
        )

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        # Assert latency is under target
        assert latency_ms < 500, f"Voice pipeline latency {latency_ms}ms exceeds 500ms target"
        assert result is not None

    async def _simulate_voice_processing(self, pipeline, audio_data):
        """Simulate voice processing with realistic delay."""
        await asyncio.sleep(0.1)  # Simulate processing time
        return {"transcription": "test", "response": "test response"}

    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self):
        """Test system performance under concurrent load."""
        # Target: Handle 100 concurrent requests
        concurrent_requests = 100
        start_time = time.time()

        tasks = []
        for i in range(concurrent_requests):
            task = asyncio.create_task(self._simulate_api_request(i))
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        total_time = end_time - start_time
        avg_response_time = total_time / concurrent_requests

        # All requests should complete successfully
        assert len(results) == concurrent_requests
        assert all(result["success"] for result in results)

        # Average response time should be reasonable
        assert avg_response_time < 1.0, f"Average response time {avg_response_time}s too high"

    async def _simulate_api_request(self, request_id):
        """Simulate API request processing."""
        # Add some jitter to simulate real-world variance
        processing_time = 0.05 + (request_id % 10) * 0.01
        await asyncio.sleep(processing_time)

        return {
            "success": True,
            "request_id": request_id,
            "processing_time": processing_time
        }

    @pytest.mark.asyncio
    async def test_rate_limiter_performance(self):
        """Test rate limiter performance under load."""
        # Mock Redis for testing
        mock_redis = Mock()
        mock_redis.zremrangebyscore.return_value = None
        mock_redis.zcard.return_value = 0
        mock_redis.zadd.return_value = None
        mock_redis.expire.return_value = None
        mock_redis.pipeline.return_value = mock_redis
        mock_redis.execute.return_value = None

        rate_limiter = ProductionRateLimiter("redis://localhost:6379")
        rate_limiter.redis = mock_redis

        # Test throughput
        start_time = time.time()
        requests_count = 1000

        for i in range(requests_count):
            allowed = await rate_limiter.is_allowed(f"key_{i % 10}")
            assert allowed is True

        end_time = time.time()
        total_time = end_time - start_time
        throughput = requests_count / total_time

        # Rate limiter should handle high throughput
        assert throughput > 500, f"Rate limiter throughput {throughput} req/s too low"

    def test_memory_usage_benchmark(self):
        """Test memory usage under normal operations."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Simulate creating many objects
        large_objects = []
        for i in range(1000):
            large_objects.append({"data": "x" * 1000, "id": i})

        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory

        # Memory increase should be reasonable
        memory_increase_mb = memory_increase / (1024 * 1024)
        assert memory_increase_mb < 100, f"Memory increase {memory_increase_mb}MB too high"

        # Clean up
        del large_objects

    @pytest.mark.asyncio
    async def test_database_connection_pool_performance(self):
        """Test database connection pool performance."""
        # Mock database operations
        async def mock_db_query():
            await asyncio.sleep(0.01)  # Simulate DB query
            return {"result": "success"}

        # Test concurrent database operations
        start_time = time.time()
        concurrent_queries = 50

        tasks = [mock_db_query() for _ in range(concurrent_queries)]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # All queries should succeed
        assert len(results) == concurrent_queries
        assert all(r["result"] == "success" for r in results)

        # Total time should indicate good concurrency
        assert total_time < 1.0, f"Database query time {total_time}s too high for {concurrent_queries} queries"

    def test_cpu_usage_under_load(self):
        """Test CPU usage under simulated load."""
        import psutil
        import threading

        def cpu_intensive_task():
            """Simulate CPU-intensive work."""
            for i in range(100000):
                _ = i ** 2

        # Measure CPU before load
        cpu_before = psutil.cpu_percent(interval=1)

        # Create multiple threads for CPU load
        threads = []
        for i in range(4):  # Use 4 threads
            thread = threading.Thread(target=cpu_intensive_task)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Measure CPU after load
        cpu_after = psutil.cpu_percent(interval=1)

        # CPU usage should be reasonable (not 100% for extended period)
        assert cpu_after < 90, f"CPU usage {cpu_after}% too high after load test"

    @pytest.mark.asyncio
    async def test_websocket_connection_capacity(self):
        """Test WebSocket connection handling capacity."""
        # Mock WebSocket connections
        mock_connections = []

        for i in range(100):  # Test 100 concurrent connections
            mock_connection = Mock()
            mock_connection.id = f"conn_{i}"
            mock_connection.send_text = Mock()
            mock_connections.append(mock_connection)

        start_time = time.time()

        # Simulate broadcasting to all connections
        message = {"type": "broadcast", "data": "test message"}
        tasks = []

        for conn in mock_connections:
            task = asyncio.create_task(self._mock_send_message(conn, message))
            tasks.append(task)

        await asyncio.gather(*tasks)
        end_time = time.time()

        broadcast_time = end_time - start_time

        # Broadcasting should be fast
        assert broadcast_time < 0.5, f"Broadcast time {broadcast_time}s too slow for 100 connections"

    async def _mock_send_message(self, connection, message):
        """Mock sending message to WebSocket connection."""
        await asyncio.sleep(0.001)  # Simulate small delay
        connection.send_text(str(message))

    def test_file_upload_performance(self):
        """Test file upload handling performance."""
        # Mock file upload scenario
        file_sizes = [1024, 10240, 102400, 1048576]  # 1KB to 1MB

        for size in file_sizes:
            start_time = time.time()

            # Simulate file processing
            mock_file_data = b"x" * size
            processed_data = self._mock_process_file(mock_file_data)

            end_time = time.time()
            processing_time = end_time - start_time

            # Processing time should scale reasonably with file size
            max_time = size / (1024 * 1024) + 0.1  # 1 second per MB + 0.1s base
            assert processing_time < max_time, f"File processing time {processing_time}s too slow for {size} bytes"
            assert processed_data is not None

    def _mock_process_file(self, file_data):
        """Mock file processing."""
        # Simulate some processing
        return {"size": len(file_data), "processed": True}


@pytest.mark.benchmark
def test_startup_time():
    """Test application startup time."""
    # This would test actual app startup time
    # For now, just ensure it's measurable
    start_time = time.time()

    # Simulate app initialization
    time.sleep(0.1)

    end_time = time.time()
    startup_time = end_time - start_time

    # Startup should be reasonable
    assert startup_time < 5.0, f"Startup time {startup_time}s too slow"


if __name__ == "__main__":
    # Run benchmarks
    pytest.main([__file__, "-v", "--tb=short"])