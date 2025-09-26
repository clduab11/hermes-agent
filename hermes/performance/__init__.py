"""
HERMES performance optimization and monitoring module.

This module provides comprehensive performance optimization including:
- Performance monitoring and metrics
- Advanced benchmarking and load testing
- Performance analysis and recommendations
- Integrated optimization suite
"""

from .performance_suite import (
    performance_suite,
    initialize_performance_suite,
    cleanup_performance_suite,
    get_performance_status,
    optimize_performance,
    benchmark_performance,
    PerformanceOptimizationSuite
)

from .advanced_benchmarks import (
    benchmark_suite,
    run_comprehensive_benchmarks,
    BenchmarkType,
    BenchmarkConfig,
    PerformanceBenchmarkSuite
)

__all__ = [
    "performance_suite",
    "initialize_performance_suite",
    "cleanup_performance_suite",
    "get_performance_status",
    "optimize_performance",
    "benchmark_performance",
    "PerformanceOptimizationSuite",
    "benchmark_suite",
    "run_comprehensive_benchmarks",
    "BenchmarkType",
    "BenchmarkConfig",
    "PerformanceBenchmarkSuite"
]