"""
Analytics Engine for HERMES Legal AI
Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.

Provides real-time and historical analytics for:
- Call statistics and conversion rates
- Voice interaction quality metrics
- Client engagement and satisfaction
- Revenue impact and ROI analysis
- System performance and usage patterns
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database.tenant_context import get_tenant_context

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics tracked by the analytics engine."""

    CALL_VOLUME = "call_volume"
    RESPONSE_TIME = "response_time"
    CONVERSION_RATE = "conversion_rate"
    CLIENT_SATISFACTION = "client_satisfaction"
    VOICE_QUALITY = "voice_quality"
    SYSTEM_PERFORMANCE = "system_performance"
    REVENUE_IMPACT = "revenue_impact"
    USER_ENGAGEMENT = "user_engagement"


class TimeRange(str, Enum):
    """Time ranges for analytics queries."""

    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


@dataclass
class AnalyticsMetric:
    """Represents a single analytics metric."""

    name: str
    value: Union[int, float, str]
    timestamp: datetime
    tenant_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    metric_type: MetricType = MetricType.SYSTEM_PERFORMANCE


@dataclass
class AnalyticsQuery:
    """Configuration for analytics queries."""

    metric_types: List[MetricType]
    time_range: TimeRange
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    tenant_id: Optional[str] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    group_by: Optional[str] = None
    aggregation: str = "sum"  # sum, avg, count, min, max


class CallStatistics(BaseModel):
    """Call statistics model."""

    total_calls: int = Field(..., description="Total number of calls")
    answered_calls: int = Field(..., description="Calls answered by AI")
    transferred_calls: int = Field(..., description="Calls transferred to humans")
    missed_calls: int = Field(..., description="Calls that were missed")
    average_duration: float = Field(..., description="Average call duration in seconds")
    conversion_rate: float = Field(..., description="Conversion rate percentage")
    client_satisfaction: float = Field(..., description="Average satisfaction score")


class VoiceMetrics(BaseModel):
    """Voice interaction quality metrics."""

    total_interactions: int = Field(..., description="Total voice interactions")
    average_response_time: float = Field(..., description="Average response time in ms")
    transcription_accuracy: float = Field(..., description="STT accuracy percentage")
    synthesis_quality: float = Field(..., description="TTS quality score")
    error_rate: float = Field(..., description="Error rate percentage")
    confidence_score: float = Field(..., description="Average AI confidence")


class RevenueMetrics(BaseModel):
    """Revenue impact analytics."""

    potential_revenue: float = Field(..., description="Potential revenue from calls")
    conversion_revenue: float = Field(..., description="Actual converted revenue")
    cost_savings: float = Field(..., description="Operational cost savings")
    roi_percentage: float = Field(..., description="Return on investment")
    billable_hours_saved: float = Field(..., description="Attorney hours saved")


class SystemPerformance(BaseModel):
    """System performance metrics."""

    uptime_percentage: float = Field(..., description="System uptime")
    average_latency: float = Field(..., description="Average API latency in ms")
    concurrent_users: int = Field(..., description="Peak concurrent users")
    resource_utilization: Dict[str, float] = Field(..., description="CPU, memory, etc.")
    error_count: int = Field(..., description="Total errors")


class AnalyticsEngine:
    """Main analytics engine for processing and aggregating metrics."""

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session
        self._metric_cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._initialized = False
        # Enable mock data only in demo/debug modes when no DB is configured
        self._mock_data_enabled = (db_session is None) and (
            settings.demo_mode or settings.debug
        )

        if db_session is None and not (settings.demo_mode or settings.debug):
            logger.warning(
                "Analytics engine initialized without database but demo mode is disabled - analytics will be unavailable"
            )
        elif self._mock_data_enabled:
            logger.warning("Analytics engine using mock data (demo/debug mode)")

    async def initialize(self):
        """Initialize the analytics engine."""
        if not self._mock_data_enabled and self.db:
            # Create analytics tables if they don't exist
            await self._ensure_analytics_tables()
        self._initialized = True
        logger.info("Analytics engine initialized")

    async def _ensure_analytics_tables(self):
        """Ensure analytics tables exist in the database."""
        try:
            # Create analytics_metrics table if it doesn't exist
            create_table_query = text(
                """
                CREATE TABLE IF NOT EXISTS analytics_metrics (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    value DECIMAL NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    tenant_id VARCHAR(100) NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    metric_type VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_analytics_tenant_time (tenant_id, timestamp),
                    INDEX idx_analytics_metric_type (metric_type),
                    INDEX idx_analytics_name (name)
                )
            """
            )
            await self.db.execute(create_table_query)
            await self.db.commit()
            logger.info("Analytics tables ensured")
        except Exception as e:
            logger.error(f"Failed to ensure analytics tables: {e}")
            await self.db.rollback()

    async def record_metric(self, metric: AnalyticsMetric) -> bool:
        """Record a new analytics metric."""
        try:
            if self._mock_data_enabled:
                # Store in memory cache for mock mode
                cache_key = (
                    f"{metric.tenant_id}:{metric.name}:{metric.timestamp.isoformat()}"
                )
                self._metric_cache[cache_key] = metric
                logger.debug(f"Recorded metric (mock): {metric.name} = {metric.value}")
                return True

            # Real database implementation
            query = text(
                """
                INSERT INTO analytics_metrics 
                (name, value, timestamp, tenant_id, metadata, metric_type)
                VALUES (:name, :value, :timestamp, :tenant_id, :metadata, :metric_type)
            """
            )

            await self.db.execute(
                query,
                {
                    "name": metric.name,
                    "value": metric.value,
                    "timestamp": metric.timestamp,
                    "tenant_id": metric.tenant_id,
                    "metadata": json.dumps(metric.metadata),
                    "metric_type": metric.metric_type.value,
                },
            )

            await self.db.commit()
            logger.debug(f"Recorded metric: {metric.name} = {metric.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
            if not self._mock_data_enabled:
                await self.db.rollback()
            return False

    async def query_metrics(self, query: AnalyticsQuery) -> List[Dict[str, Any]]:
        """Execute analytics query and return results."""
        try:
            if self._mock_data_enabled:
                # Return mock data when no database is available
                return await self._generate_mock_metrics(query)
            if self.db is None:
                logger.error(
                    "Analytics query requested but no database configured and demo mode is disabled"
                )
                return []

            # Build dynamic query based on parameters
            base_query = """
                SELECT 
                    name,
                    {aggregation}(CAST(value AS DECIMAL)) as value,
                    DATE_TRUNC('{time_range}', timestamp) as period,
                    tenant_id,
                    metric_type
                FROM analytics_metrics 
                WHERE 1=1
            """.format(
                aggregation=query.aggregation, time_range=query.time_range.value
            )

            params = {}

            # Add filters
            if query.tenant_id:
                base_query += " AND tenant_id = :tenant_id"
                params["tenant_id"] = query.tenant_id

            if query.metric_types:
                placeholders = ",".join(
                    [f":metric_type_{i}" for i in range(len(query.metric_types))]
                )
                base_query += f" AND metric_type IN ({placeholders})"
                for i, metric_type in enumerate(query.metric_types):
                    params[f"metric_type_{i}"] = metric_type.value

            if query.start_date:
                base_query += " AND timestamp >= :start_date"
                params["start_date"] = query.start_date

            if query.end_date:
                base_query += " AND timestamp <= :end_date"
                params["end_date"] = query.end_date

            # Add grouping
            group_fields = ["period", "name", "metric_type"]
            if query.tenant_id is None:
                group_fields.append("tenant_id")

            base_query += f" GROUP BY {', '.join(group_fields)}"
            base_query += " ORDER BY period DESC, name"

            result = await self.db.execute(text(base_query), params)
            rows = result.fetchall()

            return [
                {
                    "name": row.name,
                    "value": float(row.value) if row.value else 0,
                    "period": row.period.isoformat() if row.period else None,
                    "tenant_id": row.tenant_id,
                    "metric_type": row.metric_type,
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Failed to query metrics: {e}")
            return []

    async def _generate_mock_metrics(
        self, query: AnalyticsQuery
    ) -> List[Dict[str, Any]]:
        """Generate mock metrics data for testing/demo purposes."""
        mock_metrics = []
        now = datetime.utcnow()

        # Generate mock data based on query parameters
        for metric_type in query.metric_types or [MetricType.CALL_VOLUME]:
            if metric_type == MetricType.CALL_VOLUME:
                mock_metrics.extend(
                    [
                        {
                            "name": "total_calls",
                            "value": 127,
                            "period": now.isoformat(),
                            "tenant_id": query.tenant_id or "default",
                            "metric_type": metric_type.value,
                        },
                        {
                            "name": "answered_calls",
                            "value": 98,
                            "period": now.isoformat(),
                            "tenant_id": query.tenant_id or "default",
                            "metric_type": metric_type.value,
                        },
                        {
                            "name": "missed_calls",
                            "value": 29,
                            "period": now.isoformat(),
                            "tenant_id": query.tenant_id or "default",
                            "metric_type": metric_type.value,
                        },
                    ]
                )
            elif metric_type == MetricType.CONVERSION_RATE:
                mock_metrics.append(
                    {
                        "name": "conversion_rate",
                        "value": 78.5,
                        "period": now.isoformat(),
                        "tenant_id": query.tenant_id or "default",
                        "metric_type": metric_type.value,
                    }
                )
            elif metric_type == MetricType.RESPONSE_TIME:
                mock_metrics.append(
                    {
                        "name": "average_response_time",
                        "value": 245,
                        "period": now.isoformat(),
                        "tenant_id": query.tenant_id or "default",
                        "metric_type": metric_type.value,
                    }
                )
            elif metric_type == MetricType.CLIENT_SATISFACTION:
                mock_metrics.append(
                    {
                        "name": "client_satisfaction",
                        "value": 4.7,
                        "period": now.isoformat(),
                        "tenant_id": query.tenant_id or "default",
                        "metric_type": metric_type.value,
                    }
                )

        return mock_metrics

    async def get_call_statistics(
        self, tenant_id: str, time_range: TimeRange = TimeRange.DAY
    ) -> CallStatistics:
        """Get comprehensive call statistics."""
        try:
            end_time = datetime.utcnow()
            start_time = self._get_start_time(end_time, time_range)

            # Query call metrics
            query = AnalyticsQuery(
                metric_types=[MetricType.CALL_VOLUME, MetricType.CONVERSION_RATE],
                time_range=time_range,
                start_date=start_time,
                end_date=end_time,
                tenant_id=tenant_id,
            )

            metrics = await self.query_metrics(query)

            # Process metrics into statistics
            stats = {
                "total_calls": 0,
                "answered_calls": 0,
                "transferred_calls": 0,
                "missed_calls": 0,
                "average_duration": 0.0,
                "conversion_rate": 0.0,
                "client_satisfaction": 0.0,
            }

            for metric in metrics:
                if metric["name"] == "total_calls":
                    stats["total_calls"] = int(metric["value"])
                elif metric["name"] == "answered_calls":
                    stats["answered_calls"] = int(metric["value"])
                elif metric["name"] == "transferred_calls":
                    stats["transferred_calls"] = int(metric["value"])
                elif metric["name"] == "missed_calls":
                    stats["missed_calls"] = int(metric["value"])
                elif metric["name"] == "average_call_duration":
                    stats["average_duration"] = float(metric["value"])
                elif metric["name"] == "conversion_rate":
                    stats["conversion_rate"] = float(metric["value"])
                elif metric["name"] == "client_satisfaction":
                    stats["client_satisfaction"] = float(metric["value"])

            return CallStatistics(**stats)

        except Exception as e:
            logger.error(f"Failed to get call statistics: {e}")
            return CallStatistics(
                total_calls=0,
                answered_calls=0,
                transferred_calls=0,
                missed_calls=0,
                average_duration=0.0,
                conversion_rate=0.0,
                client_satisfaction=0.0,
            )

    async def get_voice_metrics(
        self, tenant_id: str, time_range: TimeRange = TimeRange.DAY
    ) -> VoiceMetrics:
        """Get voice interaction quality metrics."""
        try:
            end_time = datetime.utcnow()
            start_time = self._get_start_time(end_time, time_range)

            query = AnalyticsQuery(
                metric_types=[MetricType.VOICE_QUALITY, MetricType.RESPONSE_TIME],
                time_range=time_range,
                start_date=start_time,
                end_date=end_time,
                tenant_id=tenant_id,
            )

            metrics = await self.query_metrics(query)

            # Process voice metrics
            voice_stats = {
                "total_interactions": 0,
                "average_response_time": 0.0,
                "transcription_accuracy": 0.0,
                "synthesis_quality": 0.0,
                "error_rate": 0.0,
                "confidence_score": 0.0,
            }

            for metric in metrics:
                if metric["name"] == "total_voice_interactions":
                    voice_stats["total_interactions"] = int(metric["value"])
                elif metric["name"] == "average_response_time":
                    voice_stats["average_response_time"] = float(metric["value"])
                elif metric["name"] == "transcription_accuracy":
                    voice_stats["transcription_accuracy"] = float(metric["value"])
                elif metric["name"] == "synthesis_quality":
                    voice_stats["synthesis_quality"] = float(metric["value"])
                elif metric["name"] == "error_rate":
                    voice_stats["error_rate"] = float(metric["value"])
                elif metric["name"] == "ai_confidence_score":
                    voice_stats["confidence_score"] = float(metric["value"])

            return VoiceMetrics(**voice_stats)

        except Exception as e:
            logger.error(f"Failed to get voice metrics: {e}")
            return VoiceMetrics(
                total_interactions=0,
                average_response_time=0.0,
                transcription_accuracy=0.0,
                synthesis_quality=0.0,
                error_rate=0.0,
                confidence_score=0.0,
            )

    async def get_revenue_metrics(
        self, tenant_id: str, time_range: TimeRange = TimeRange.MONTH
    ) -> RevenueMetrics:
        """Get revenue impact analytics."""
        try:
            end_time = datetime.utcnow()
            start_time = self._get_start_time(end_time, time_range)

            query = AnalyticsQuery(
                metric_types=[MetricType.REVENUE_IMPACT],
                time_range=time_range,
                start_date=start_time,
                end_date=end_time,
                tenant_id=tenant_id,
            )

            metrics = await self.query_metrics(query)

            # Process revenue metrics
            revenue_stats = {
                "potential_revenue": 0.0,
                "conversion_revenue": 0.0,
                "cost_savings": 0.0,
                "roi_percentage": 0.0,
                "billable_hours_saved": 0.0,
            }

            for metric in metrics:
                if metric["name"] == "potential_revenue":
                    revenue_stats["potential_revenue"] = float(metric["value"])
                elif metric["name"] == "conversion_revenue":
                    revenue_stats["conversion_revenue"] = float(metric["value"])
                elif metric["name"] == "cost_savings":
                    revenue_stats["cost_savings"] = float(metric["value"])
                elif metric["name"] == "roi_percentage":
                    revenue_stats["roi_percentage"] = float(metric["value"])
                elif metric["name"] == "billable_hours_saved":
                    revenue_stats["billable_hours_saved"] = float(metric["value"])

            return RevenueMetrics(**revenue_stats)

        except Exception as e:
            logger.error(f"Failed to get revenue metrics: {e}")
            return RevenueMetrics(
                potential_revenue=0.0,
                conversion_revenue=0.0,
                cost_savings=0.0,
                roi_percentage=0.0,
                billable_hours_saved=0.0,
            )

    async def get_system_performance(
        self, time_range: TimeRange = TimeRange.HOUR
    ) -> SystemPerformance:
        """Get system performance metrics."""
        try:
            end_time = datetime.utcnow()
            start_time = self._get_start_time(end_time, time_range)

            query = AnalyticsQuery(
                metric_types=[MetricType.SYSTEM_PERFORMANCE],
                time_range=time_range,
                start_date=start_time,
                end_date=end_time,
                aggregation="avg",
            )

            metrics = await self.query_metrics(query)

            # Process system metrics
            performance_stats = {
                "uptime_percentage": 100.0,
                "average_latency": 0.0,
                "concurrent_users": 0,
                "resource_utilization": {"cpu": 0.0, "memory": 0.0, "disk": 0.0},
                "error_count": 0,
            }

            for metric in metrics:
                if metric["name"] == "uptime_percentage":
                    performance_stats["uptime_percentage"] = float(metric["value"])
                elif metric["name"] == "average_latency":
                    performance_stats["average_latency"] = float(metric["value"])
                elif metric["name"] == "concurrent_users":
                    performance_stats["concurrent_users"] = int(metric["value"])
                elif metric["name"] == "cpu_utilization":
                    performance_stats["resource_utilization"]["cpu"] = float(
                        metric["value"]
                    )
                elif metric["name"] == "memory_utilization":
                    performance_stats["resource_utilization"]["memory"] = float(
                        metric["value"]
                    )
                elif metric["name"] == "disk_utilization":
                    performance_stats["resource_utilization"]["disk"] = float(
                        metric["value"]
                    )
                elif metric["name"] == "error_count":
                    performance_stats["error_count"] = int(metric["value"])

            return SystemPerformance(**performance_stats)

        except Exception as e:
            logger.error(f"Failed to get system performance: {e}")
            return SystemPerformance(
                uptime_percentage=100.0,
                average_latency=0.0,
                concurrent_users=0,
                resource_utilization={},
                error_count=0,
            )

    async def generate_analytics_report(
        self, tenant_id: str, time_range: TimeRange = TimeRange.WEEK
    ) -> Dict[str, Any]:
        """Generate comprehensive analytics report."""
        try:
            # Gather all metrics in parallel
            (
                call_stats,
                voice_metrics,
                revenue_metrics,
                system_performance,
            ) = await asyncio.gather(
                self.get_call_statistics(tenant_id, time_range),
                self.get_voice_metrics(tenant_id, time_range),
                self.get_revenue_metrics(tenant_id, time_range),
                self.get_system_performance(time_range),
            )

            # Calculate trends and insights
            insights = await self._generate_insights(tenant_id, time_range)

            return {
                "tenant_id": tenant_id,
                "time_range": time_range.value,
                "generated_at": datetime.utcnow().isoformat(),
                "call_statistics": call_stats.model_dump(),
                "voice_metrics": voice_metrics.model_dump(),
                "revenue_metrics": revenue_metrics.model_dump(),
                "system_performance": system_performance.model_dump(),
                "insights": insights,
            }

        except Exception as e:
            logger.error(f"Failed to generate analytics report: {e}")
            return {
                "error": "Failed to generate analytics report",
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _get_start_time(self, end_time: datetime, time_range: TimeRange) -> datetime:
        """Calculate start time based on time range."""
        if time_range == TimeRange.HOUR:
            return end_time - timedelta(hours=1)
        elif time_range == TimeRange.DAY:
            return end_time - timedelta(days=1)
        elif time_range == TimeRange.WEEK:
            return end_time - timedelta(weeks=1)
        elif time_range == TimeRange.MONTH:
            return end_time - timedelta(days=30)
        elif time_range == TimeRange.QUARTER:
            return end_time - timedelta(days=90)
        elif time_range == TimeRange.YEAR:
            return end_time - timedelta(days=365)
        else:
            return end_time - timedelta(days=1)

    async def _generate_insights(
        self, tenant_id: str, time_range: TimeRange
    ) -> List[Dict[str, Any]]:
        """Generate actionable insights from analytics data."""
        insights = []

        try:
            # Get historical data for comparison
            current_stats = await self.get_call_statistics(tenant_id, time_range)

            # Example insights
            if current_stats.conversion_rate < 50:
                insights.append(
                    {
                        "type": "warning",
                        "title": "Low Conversion Rate",
                        "description": f"Current conversion rate is {current_stats.conversion_rate:.1f}%, below optimal range",
                        "recommendation": "Review call handling procedures and consider additional training",
                        "priority": "high",
                    }
                )

            if current_stats.missed_calls > current_stats.total_calls * 0.1:
                insights.append(
                    {
                        "type": "alert",
                        "title": "High Missed Call Rate",
                        "description": f"{current_stats.missed_calls} calls missed out of {current_stats.total_calls} total",
                        "recommendation": "Check system availability and consider capacity scaling",
                        "priority": "critical",
                    }
                )

            if current_stats.client_satisfaction > 4.5:
                insights.append(
                    {
                        "type": "success",
                        "title": "Excellent Client Satisfaction",
                        "description": f"Client satisfaction score of {current_stats.client_satisfaction:.1f}/5.0",
                        "recommendation": "Continue current practices and consider sharing best practices",
                        "priority": "low",
                    }
                )

        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            insights.append(
                {
                    "type": "error",
                    "title": "Insights Generation Error",
                    "description": "Unable to generate insights from current data",
                    "recommendation": "Check analytics data collection and processing",
                    "priority": "medium",
                }
            )

        return insights


class RealTimeAnalytics:
    """Real-time analytics processing and streaming."""

    def __init__(self):
        self._active_sessions = {}
        self._metric_buffer = []
        self._buffer_size = 1000

    async def start_real_time_processing(self):
        """Start real-time analytics processing."""
        asyncio.create_task(self._process_metrics_buffer())
        logger.info("Real-time analytics processing started")

    async def add_real_time_metric(self, metric: AnalyticsMetric):
        """Add metric to real-time processing queue."""
        self._metric_buffer.append(metric)

        # Process buffer if it's full
        if len(self._metric_buffer) >= self._buffer_size:
            await self._process_metrics_buffer()

    async def _process_metrics_buffer(self):
        """Process buffered metrics."""
        if not self._metric_buffer:
            return

        try:
            # Process metrics in batches
            batch_size = 100
            for i in range(0, len(self._metric_buffer), batch_size):
                batch = self._metric_buffer[i : i + batch_size]
                await self._process_metric_batch(batch)

            # Clear processed metrics
            self._metric_buffer.clear()

        except Exception as e:
            logger.error(f"Failed to process metrics buffer: {e}")

    async def _process_metric_batch(self, metrics: List[AnalyticsMetric]):
        """Process a batch of metrics."""
        # This would typically update real-time dashboards,
        # trigger alerts, or update aggregations
        for metric in metrics:
            logger.debug(f"Processing real-time metric: {metric.name}")
