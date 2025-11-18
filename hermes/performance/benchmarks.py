"""
Performance Benchmarking Utilities for Legal AI System
Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.

Provides comprehensive performance benchmarking and profiling tools.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import statistics

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result from a performance benchmark"""
    name: str
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    std_dev_ms: float
    iterations: int
    success_rate: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceBenchmark:
    """
    Performance benchmarking utility for legal AI components.

    Measures:
    - Execution time (avg, min, max, std dev)
    - Success rate
    - Memory usage (optional)
    - Throughput
    """

    def __init__(self):
        self.results: List[BenchmarkResult] = []

    async def benchmark_async(
        self,
        name: str,
        func: Callable,
        iterations: int = 100,
        warmup: int = 10,
        **kwargs
    ) -> BenchmarkResult:
        """
        Benchmark an async function.

        Args:
            name: Benchmark name
            func: Async function to benchmark
            iterations: Number of iterations
            warmup: Warmup iterations (not counted)
            **kwargs: Arguments to pass to function

        Returns:
            BenchmarkResult with timing statistics
        """
        # Warmup
        for _ in range(warmup):
            try:
                await func(**kwargs)
            except Exception:
                pass

        # Benchmark
        times = []
        successes = 0

        for _ in range(iterations):
            start = time.perf_counter()
            try:
                await func(**kwargs)
                successes += 1
            except Exception as e:
                logger.warning(f"Benchmark error: {e}")

            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            times.append(elapsed)

        # Calculate statistics
        total_time = sum(times)
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        success_rate = successes / iterations

        result = BenchmarkResult(
            name=name,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            std_dev_ms=std_dev,
            iterations=iterations,
            success_rate=success_rate
        )

        self.results.append(result)
        return result

    def benchmark_sync(
        self,
        name: str,
        func: Callable,
        iterations: int = 100,
        warmup: int = 10,
        **kwargs
    ) -> BenchmarkResult:
        """Benchmark a synchronous function"""
        # Warmup
        for _ in range(warmup):
            try:
                func(**kwargs)
            except Exception:
                pass

        # Benchmark
        times = []
        successes = 0

        for _ in range(iterations):
            start = time.perf_counter()
            try:
                func(**kwargs)
                successes += 1
            except Exception:
                pass

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        total_time = sum(times)
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        success_rate = successes / iterations

        result = BenchmarkResult(
            name=name,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            std_dev_ms=std_dev,
            iterations=iterations,
            success_rate=success_rate
        )

        self.results.append(result)
        return result

    def print_results(self):
        """Print benchmark results in a formatted table"""
        lines = []
        lines.append("\n" + "="*80)
        lines.append("PERFORMANCE BENCHMARK RESULTS")
        lines.append("="*80)
        lines.append("")

        lines.append(f"{'Benchmark':<40} {'Avg (ms)':<12} {'Min (ms)':<12} {'Max (ms)':<12} {'Success %':<10}")
        lines.append("-"*80)

        for result in self.results:
            lines.append(
                f"{result.name:<40} "
                f"{result.avg_time_ms:<12.2f} "
                f"{result.min_time_ms:<12.2f} "
                f"{result.max_time_ms:<12.2f} "
                f"{result.success_rate*100:<10.1f}"
            )

        lines.append("="*80)
        lines.append("")

        for line in lines:
            logger.info(line)

    def generate_report(self) -> str:
        """Generate a detailed performance report"""
        report = []
        report.append("="*80)
        report.append("LEGAL AI SYSTEM - PERFORMANCE BENCHMARK REPORT")
        report.append("="*80)
        report.append(f"Generated: {datetime.utcnow().isoformat()}")
        report.append(f"Total Benchmarks: {len(self.results)}")
        report.append("")

        for result in self.results:
            report.append(f"Benchmark: {result.name}")
            report.append(f"  Iterations: {result.iterations}")
            report.append(f"  Average Time: {result.avg_time_ms:.2f} ms")
            report.append(f"  Min Time: {result.min_time_ms:.2f} ms")
            report.append(f"  Max Time: {result.max_time_ms:.2f} ms")
            report.append(f"  Std Dev: {result.std_dev_ms:.2f} ms")
            report.append(f"  Success Rate: {result.success_rate*100:.1f}%")
            report.append(f"  Total Time: {result.total_time_ms:.2f} ms")
            report.append("")

        # Summary statistics
        if self.results:
            avg_times = [r.avg_time_ms for r in self.results]
            report.append("SUMMARY STATISTICS")
            report.append(f"  Overall Avg: {statistics.mean(avg_times):.2f} ms")
            report.append(f"  Overall Min: {min(avg_times):.2f} ms")
            report.append(f"  Overall Max: {max(avg_times):.2f} ms")
            report.append("")

        report.append("="*80)

        return "\n".join(report)


async def benchmark_legal_ai_system():
    """
    Comprehensive benchmark of the legal AI system.

    Tests:
    - Legal reasoning engine
    - Citation graph operations
    - Security operations
    - Database queries
    """
    from hermes.reasoning.legal_reasoning_engine import LegalReasoningEngine, LegalDomain
    from hermes.reasoning.citation_graph import CitationGraph, CaseNode
    from hermes.security.legal_security import LegalAISecurityManager

    benchmark = PerformanceBenchmark()

    logger.info("Starting comprehensive performance benchmarks...")

    # Initialize components
    engine = LegalReasoningEngine()
    graph = CitationGraph()
    security = LegalAISecurityManager()

    # Benchmark 1: Legal reasoning analysis
    logger.info("Benchmarking legal reasoning engine...")

    async def run_reasoning():
        await engine.analyze_legal_query(
            query="Simple negligence case analysis",
            domain=LegalDomain.TORT_LAW,
            jurisdiction="California",
            max_citations=5
        )

    await benchmark.benchmark_async(
        "Legal Reasoning Analysis",
        run_reasoning,
        iterations=10,  # Reduced for speed
        warmup=2
    )

    # Benchmark 2: Citation graph PageRank
    logger.info("Benchmarking citation graph PageRank...")

    # Add sample nodes
    for i in range(10):
        graph.add_node(CaseNode(
            case_id=f"case_{i}",
            case_name=f"Test Case {i}",
            year=2020 + i,
            court="Test Court",
            jurisdiction="Test"
        ))

    def run_pagerank():
        graph.compute_pagerank()

    benchmark.benchmark_sync(
        "Citation Graph PageRank",
        run_pagerank,
        iterations=50,
        warmup=5
    )

    # Benchmark 3: Encryption operations
    logger.info("Benchmarking encryption...")

    test_data = "Attorney-client privileged communication" * 10

    def run_encryption():
        encrypted = security.encryption.encrypt(test_data)
        security.encryption.decrypt(encrypted)

    benchmark.benchmark_sync(
        "Encryption/Decryption",
        run_encryption,
        iterations=100,
        warmup=10
    )

    # Benchmark 4: Audit logging
    logger.info("Benchmarking audit logging...")

    async def run_audit_log():
        await security.audit_log.log_event(
            event_type="ACCESS",
            user_id="test_user",
            user_email="test@example.com",
            resource_type="test",
            resource_id="test_123",
            action="read",
            success=True
        )

    await benchmark.benchmark_async(
        "Audit Log Entry",
        run_audit_log,
        iterations=100,
        warmup=10
    )

    # Print results
    benchmark.print_results()

    # Generate detailed report
    report = benchmark.generate_report()

    return report


if __name__ == "__main__":
    # Run benchmarks
    report = asyncio.run(benchmark_legal_ai_system())

    # Save report
    with open("performance_benchmark_report.txt", "w") as f:
        f.write(report)

    logger.info("Detailed report saved to: performance_benchmark_report.txt")
