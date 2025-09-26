"""
HERMES SaaS Usage Tracking and Billing Enforcement
Copyright (c) 2024 Parallax Analytics LLC. All rights reserved.

This module enforces usage limits and billing for the SaaS platform.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

import httpx
import structlog
from fastapi import HTTPException

logger = structlog.get_logger(__name__)

@dataclass
class UsageMetric:
    """Usage metric for tracking billable events."""
    tenant_id: str
    metric_type: str  # voice_call, api_request, storage_mb, etc.
    quantity: int
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class UsageLimits:
    """Usage limits for a tenant."""
    max_voice_calls_per_hour: int
    max_api_requests_per_hour: int
    max_storage_mb: int
    max_concurrent_sessions: int

class UsageEnforcer:
    """Enforces usage limits and tracks billing for SaaS tenants."""

    def __init__(self):
        self.usage_cache = {}
        self.tenant_limits = {}
        self.billing_queue = []
        self.enforcement_enabled = True
        self._billing_task = None

    async def initialize(self):
        """Initialize usage enforcement."""
        logger.info("Initializing usage enforcement and billing")

        # Start billing background task
        self._billing_task = asyncio.create_task(self._billing_loop())

    async def track_usage(self, tenant_id: str, metric_type: str,
                         quantity: int = 1, metadata: Dict[str, Any] = None) -> bool:
        """Track usage and enforce limits."""

        if not self.enforcement_enabled:
            return True

        try:
            # Create usage metric
            metric = UsageMetric(
                tenant_id=tenant_id,
                metric_type=metric_type,
                quantity=quantity,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )

            # Check usage limits
            if not await self._check_usage_limits(metric):
                logger.warning(f"Usage limit exceeded for {tenant_id}: {metric_type}")
                return False

            # Record usage
            await self._record_usage(metric)

            # Queue for billing
            self.billing_queue.append(metric)

            return True

        except Exception as e:
            logger.error(f"Usage tracking error: {e}")
            # In error cases, allow usage but log
            return True

    async def _check_usage_limits(self, metric: UsageMetric) -> bool:
        """Check if usage is within limits."""

        tenant_id = metric.tenant_id
        limits = await self._get_tenant_limits(tenant_id)

        if not limits:
            logger.warning(f"No limits found for tenant {tenant_id}")
            return True

        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

        # Get current hour usage
        hour_usage = await self._get_hourly_usage(tenant_id, current_hour)

        # Check specific limits
        if metric.metric_type == "voice_call":
            if hour_usage.get("voice_call", 0) >= limits.max_voice_calls_per_hour:
                await self._send_usage_alert(tenant_id, "voice_call", "hourly_limit_reached")
                return False

        elif metric.metric_type == "api_request":
            if hour_usage.get("api_request", 0) >= limits.max_api_requests_per_hour:
                await self._send_usage_alert(tenant_id, "api_request", "hourly_limit_reached")
                return False

        elif metric.metric_type == "concurrent_session":
            current_sessions = await self._get_current_sessions(tenant_id)
            if current_sessions >= limits.max_concurrent_sessions:
                return False

        return True

    async def _get_tenant_limits(self, tenant_id: str) -> Optional[UsageLimits]:
        """Get usage limits for a tenant."""

        # Check cache first
        if tenant_id in self.tenant_limits:
            cached = self.tenant_limits[tenant_id]
            if cached["expires"] > datetime.utcnow():
                return cached["limits"]

        # Fetch from billing service
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"https://billing.hermes.parallax-ai.app/tenant/{tenant_id}/limits",
                    headers={"Authorization": f"Bearer {self._get_service_token()}"}
                )

                if response.status_code == 200:
                    data = response.json()
                    limits = UsageLimits(
                        max_voice_calls_per_hour=data.get("max_voice_calls_per_hour", 1000),
                        max_api_requests_per_hour=data.get("max_api_requests_per_hour", 10000),
                        max_storage_mb=data.get("max_storage_mb", 10000),
                        max_concurrent_sessions=data.get("max_concurrent_sessions", 100)
                    )

                    # Cache for 10 minutes
                    self.tenant_limits[tenant_id] = {
                        "limits": limits,
                        "expires": datetime.utcnow() + timedelta(minutes=10)
                    }

                    return limits

                else:
                    logger.warning(f"Failed to get limits for tenant {tenant_id}: {response.status_code}")

        except Exception as e:
            logger.error(f"Error fetching tenant limits: {e}")

        # Return default limits
        return UsageLimits(
            max_voice_calls_per_hour=100,
            max_api_requests_per_hour=1000,
            max_storage_mb=1000,
            max_concurrent_sessions=10
        )

    async def _get_hourly_usage(self, tenant_id: str, hour: datetime) -> Dict[str, int]:
        """Get usage for specific hour."""

        cache_key = f"{tenant_id}:{hour.isoformat()}"

        if cache_key in self.usage_cache:
            return self.usage_cache[cache_key]

        # Initialize empty usage
        usage = {
            "voice_call": 0,
            "api_request": 0,
            "storage_mb": 0
        }

        self.usage_cache[cache_key] = usage
        return usage

    async def _record_usage(self, metric: UsageMetric):
        """Record usage metric."""

        hour = metric.timestamp.replace(minute=0, second=0, microsecond=0)
        cache_key = f"{metric.tenant_id}:{hour.isoformat()}"

        # Update cache
        if cache_key not in self.usage_cache:
            self.usage_cache[cache_key] = {}

        current_usage = self.usage_cache[cache_key].get(metric.metric_type, 0)
        self.usage_cache[cache_key][metric.metric_type] = current_usage + metric.quantity

        # Log usage
        logger.info(
            "Usage recorded",
            tenant=metric.tenant_id,
            metric=metric.metric_type,
            quantity=metric.quantity,
            total=self.usage_cache[cache_key][metric.metric_type]
        )

    async def _get_current_sessions(self, tenant_id: str) -> int:
        """Get current active sessions for tenant."""
        # This would integrate with session manager
        # For now, return mock value
        return 0

    async def _send_usage_alert(self, tenant_id: str, metric_type: str, alert_type: str):
        """Send usage alert to tenant."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    "https://notifications.hermes.parallax-ai.app/usage-alert",
                    json={
                        "tenant_id": tenant_id,
                        "metric_type": metric_type,
                        "alert_type": alert_type,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    headers={"Authorization": f"Bearer {self._get_service_token()}"}
                )
        except Exception as e:
            logger.error(f"Failed to send usage alert: {e}")

    async def _billing_loop(self):
        """Background task for processing billing."""
        while True:
            try:
                await asyncio.sleep(60)  # Process billing every minute

                if not self.billing_queue:
                    continue

                # Process billing queue
                batch = self.billing_queue.copy()
                self.billing_queue.clear()

                await self._process_billing_batch(batch)

            except Exception as e:
                logger.error(f"Billing loop error: {e}")

    async def _process_billing_batch(self, metrics: List[UsageMetric]):
        """Process a batch of usage metrics for billing."""

        if not metrics:
            return

        try:
            # Group by tenant
            tenant_usage = {}
            for metric in metrics:
                if metric.tenant_id not in tenant_usage:
                    tenant_usage[metric.tenant_id] = []
                tenant_usage[metric.tenant_id].append(metric)

            # Send to billing service
            for tenant_id, usage_metrics in tenant_usage.items():
                await self._submit_usage_to_billing(tenant_id, usage_metrics)

        except Exception as e:
            logger.error(f"Billing batch processing error: {e}")

    async def _submit_usage_to_billing(self, tenant_id: str, metrics: List[UsageMetric]):
        """Submit usage metrics to billing service."""

        try:
            usage_data = []
            for metric in metrics:
                usage_data.append({
                    "metric_type": metric.metric_type,
                    "quantity": metric.quantity,
                    "timestamp": metric.timestamp.isoformat(),
                    "metadata": metric.metadata
                })

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"https://billing.hermes.parallax-ai.app/usage/{tenant_id}",
                    json={"usage_data": usage_data},
                    headers={"Authorization": f"Bearer {self._get_service_token()}"}
                )

                if response.status_code == 200:
                    logger.info(f"Submitted {len(metrics)} usage metrics for tenant {tenant_id}")
                else:
                    logger.error(f"Billing submission failed: {response.status_code} {response.text}")

        except Exception as e:
            logger.error(f"Failed to submit usage to billing: {e}")

    def _get_service_token(self) -> str:
        """Get service authentication token."""
        # This would fetch from secure secrets
        import os
        return os.getenv("HERMES_SERVICE_TOKEN", "service-token-placeholder")

    async def get_usage_summary(self, tenant_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get usage summary for tenant."""

        summary = {
            "tenant_id": tenant_id,
            "period_hours": hours,
            "usage": {
                "voice_calls": 0,
                "api_requests": 0,
                "storage_mb": 0
            },
            "limits": None
        }

        try:
            # Get limits
            limits = await self._get_tenant_limits(tenant_id)
            if limits:
                summary["limits"] = {
                    "max_voice_calls_per_hour": limits.max_voice_calls_per_hour,
                    "max_api_requests_per_hour": limits.max_api_requests_per_hour,
                    "max_storage_mb": limits.max_storage_mb,
                    "max_concurrent_sessions": limits.max_concurrent_sessions
                }

            # Calculate usage over period
            now = datetime.utcnow()
            start_hour = now - timedelta(hours=hours)

            current_hour = start_hour.replace(minute=0, second=0, microsecond=0)
            while current_hour <= now:
                hourly_usage = await self._get_hourly_usage(tenant_id, current_hour)

                summary["usage"]["voice_calls"] += hourly_usage.get("voice_call", 0)
                summary["usage"]["api_requests"] += hourly_usage.get("api_request", 0)
                summary["usage"]["storage_mb"] += hourly_usage.get("storage_mb", 0)

                current_hour += timedelta(hours=1)

        except Exception as e:
            logger.error(f"Error getting usage summary: {e}")

        return summary

    async def enforce_billing_status(self, tenant_id: str) -> bool:
        """Check if tenant's billing is current and enforce access."""

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"https://billing.hermes.parallax-ai.app/tenant/{tenant_id}/status",
                    headers={"Authorization": f"Bearer {self._get_service_token()}"}
                )

                if response.status_code == 200:
                    data = response.json()
                    billing_status = data.get("status", "unknown")

                    if billing_status in ["current", "trial"]:
                        return True
                    elif billing_status == "past_due":
                        logger.warning(f"Tenant {tenant_id} has past due billing")
                        return False
                    elif billing_status == "suspended":
                        logger.error(f"Tenant {tenant_id} is suspended for billing")
                        return False

                else:
                    logger.warning(f"Could not verify billing status for {tenant_id}")
                    # Allow access if billing service is down
                    return True

        except Exception as e:
            logger.error(f"Billing status check failed: {e}")
            # Allow access if service is down
            return True

        return False

# Global usage enforcer instance
usage_enforcer = UsageEnforcer()

# Decorator for usage-limited endpoints
def track_usage(metric_type: str, quantity: int = 1):
    """Decorator to track usage on endpoints."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract tenant_id from request or auth context
            tenant_id = "default"  # Would be extracted from auth context

            # Check billing status first
            if not await usage_enforcer.enforce_billing_status(tenant_id):
                raise HTTPException(
                    status_code=402,
                    detail="Payment required - please update billing information"
                )

            # Track usage
            if not await usage_enforcer.track_usage(tenant_id, metric_type, quantity):
                raise HTTPException(
                    status_code=429,
                    detail=f"Usage limit exceeded for {metric_type}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator