"""
HERMES optimization module.

This module provides advanced optimization capabilities including:
- Memory management and garbage collection
- Resource optimization
- Performance tuning
- Memory leak detection
"""

from .memory_manager import (
    memory_manager,
    initialize_memory_manager,
    cleanup_memory_manager,
    optimize_memory,
    get_memory_status,
    MemoryPressureLevel,
    MemoryManager,
    memory_optimized,
    cached_method
)

__all__ = [
    "memory_manager",
    "initialize_memory_manager",
    "cleanup_memory_manager",
    "optimize_memory",
    "get_memory_status",
    "MemoryPressureLevel",
    "MemoryManager",
    "memory_optimized",
    "cached_method"
]