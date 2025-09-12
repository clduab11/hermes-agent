"""
Analytics API endpoints for HERMES Legal AI Dashboard
Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.

Provides real-time analytics data for the dashboard:
- Call statistics and metrics
- Voice quality metrics
- Revenue impact analytics
- System performance data
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ..auth.middleware import get_current_user, require_permission
from ..database.tenant_context import get_tenant_context
from ..analytics.engine import AnalyticsEngine, TimeRange

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard/overview")
async def get_dashboard_overview(
    time_range: TimeRange = Query(TimeRange.DAY, description="Time range for metrics"),
    current_user = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
    _: None = Depends(require_permission("analytics:read"))
):
    """Get dashboard overview data."""
    try:
        # Mock data for dashboard - in production this would use AnalyticsEngine
        overview_data = {
            "total_calls": 127,
            "calls_trend": "+12%",
            "conversion_rate": 78.5,
            "conversion_trend": "+5%", 
            "response_time": 245,
            "response_trend": "-15ms",
            "satisfaction": 4.7,
            "satisfaction_trend": "+0.2"
        }
        
        return {
            "status": "success",
            "data": overview_data,
            "time_range": time_range.value,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard overview")


@router.get("/dashboard/charts/call-volume")
async def get_call_volume_chart(
    time_range: TimeRange = Query(TimeRange.WEEK, description="Time range for chart"),
    current_user = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
    _: None = Depends(require_permission("analytics:read"))
):
    """Get call volume chart data."""
    try:
        # Mock chart data
        chart_data = {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "datasets": [{
                "label": "Calls",
                "data": [45, 52, 38, 67, 73, 29, 34],
                "backgroundColor": "rgba(59, 130, 246, 0.1)",
                "borderColor": "rgb(59, 130, 246)",
                "borderWidth": 2,
                "fill": True
            }]
        }
        
        return {
            "status": "success", 
            "data": chart_data,
            "time_range": time_range.value
        }
        
    except Exception as e:
        logger.error(f"Failed to get call volume chart: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve call volume chart")


@router.get("/dashboard/charts/revenue")
async def get_revenue_chart(
    time_range: TimeRange = Query(TimeRange.MONTH, description="Time range for chart"),
    current_user = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
    _: None = Depends(require_permission("analytics:read"))
):
    """Get revenue impact chart data."""
    try:
        # Mock revenue chart data
        chart_data = {
            "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
            "datasets": [
                {
                    "label": "Potential Revenue",
                    "data": [12500, 15200, 18900, 16700],
                    "backgroundColor": "rgba(251, 191, 36, 0.1)",
                    "borderColor": "rgb(251, 191, 36)",
                    "borderWidth": 2
                },
                {
                    "label": "Converted Revenue", 
                    "data": [8750, 11400, 14200, 12300],
                    "backgroundColor": "rgba(34, 197, 94, 0.1)",
                    "borderColor": "rgb(34, 197, 94)",
                    "borderWidth": 2
                }
            ]
        }
        
        return {
            "status": "success",
            "data": chart_data,
            "time_range": time_range.value
        }
        
    except Exception as e:
        logger.error(f"Failed to get revenue chart: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve revenue chart")


@router.get("/dashboard/recent-activity")
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50, description="Number of activities to return"),
    current_user = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
    _: None = Depends(require_permission("analytics:read"))
):
    """Get recent activity feed for dashboard."""
    try:
        # Mock recent activity data
        activities = [
            {
                "id": "activity_1",
                "type": "voice_call",
                "description": "Voice interaction completed with high satisfaction",
                "timestamp": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
                "user": "System",
                "details": {
                    "duration": "2m 45s",
                    "satisfaction": 4.8,
                    "converted": True
                }
            },
            {
                "id": "activity_2", 
                "type": "client_update",
                "description": "New client record created: Johnson Law Firm",
                "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "user": current_user.email,
                "details": {
                    "client_id": "client_123",
                    "practice_area": "Corporate Law"
                }
            },
            {
                "id": "activity_3",
                "type": "system_alert",
                "description": "Voice response time improved by 15ms", 
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "user": "System",
                "details": {
                    "old_time": "260ms",
                    "new_time": "245ms",
                    "improvement": "15ms"
                }
            },
            {
                "id": "activity_4",
                "type": "integration",
                "description": "Clio sync completed successfully",
                "timestamp": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
                "user": "Integration",
                "details": {
                    "synced_records": 45,
                    "status": "success"
                }
            }
        ]
        
        return {
            "status": "success",
            "data": activities[:limit],
            "total_count": len(activities)
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recent activity")


@router.get("/system/performance")
async def get_system_performance(
    current_user = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
    _: None = Depends(require_permission("analytics:read"))
):
    """Get real-time system performance metrics."""
    try:
        # Mock system performance data
        performance_data = {
            "uptime": "99.9%",
            "response_time": "245ms",
            "concurrent_users": 23,
            "voice_system": {
                "status": "healthy",
                "stt_latency": "180ms",
                "tts_latency": "95ms", 
                "ai_confidence": 0.92
            },
            "resource_utilization": {
                "cpu": 32.5,
                "memory": 48.2,
                "disk": 67.1
            },
            "integrations": {
                "clio": "connected",
                "mcp_servers": 8,
                "healthy_servers": 8
            }
        }
        
        return {
            "status": "success",
            "data": performance_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system performance")


@router.get("/voice/status")
async def get_voice_system_status(
    current_user = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context)
):
    """Get voice system status for dashboard indicator."""
    try:
        # Mock voice system status
        voice_status = {
            "status": "ready",
            "indicator_color": "green",
            "status_text": "Voice Ready",
            "last_interaction": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
            "health_score": 0.95,
            "active_sessions": 2
        }
        
        return {
            "status": "success",
            "data": voice_status
        }
        
    except Exception as e:
        logger.error(f"Failed to get voice system status: {e}")
        # Return degraded status on error
        return {
            "status": "success",
            "data": {
                "status": "degraded",
                "indicator_color": "yellow", 
                "status_text": "Voice Degraded",
                "health_score": 0.5,
                "active_sessions": 0
            }
        }