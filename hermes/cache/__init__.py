"""
HERMES cache management module.

This module provides comprehensive caching solutions including:
- Multi-level caching (memory + Redis)
- Tenant-aware cache isolation
- Performance optimization
- Cache analytics and monitoring
"""

from .tenant_cache_manager import (
    tenant_cache_manager,
    init_tenant_cache,
    close_tenant_cache,
    CacheLevel,
    CacheMetrics,
    TenantCacheManager
)

__all__ = [
    "tenant_cache_manager",
    "init_tenant_cache",
    "close_tenant_cache",
    "CacheLevel",
    "CacheMetrics",
    "TenantCacheManager"
]