"""
HERMES auto-scaling and resource management module.

This module provides enterprise-grade auto-scaling capabilities including:
- Automatic horizontal scaling based on metrics
- Resource optimization and monitoring
- Cloud platform integration
- Performance-based scaling decisions
"""

from .auto_scaler import (
    auto_scaler,
    initialize_auto_scaler,
    cleanup_auto_scaler,
    get_scaling_status,
    ScalingDirection,
    MemoryPressureLevel,
    AutoScaler
)

__all__ = [
    "auto_scaler",
    "initialize_auto_scaler",
    "cleanup_auto_scaler",
    "get_scaling_status",
    "ScalingDirection",
    "MemoryPressureLevel",
    "AutoScaler"
]