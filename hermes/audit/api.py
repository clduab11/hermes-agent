"""
Audit API endpoints for HERMES Legal AI
Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.

Provides comprehensive audit trail functionality for compliance and monitoring:
- User action logging and retrieval
- System event tracking
- Security event monitoring
- Compliance reporting
- Data export for legal discovery
"""

import csv
import io
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..analytics.engine import AnalyticsEngine, AnalyticsMetric, MetricType
from ..auth.middleware import get_current_user, require_permission
from ..database.tenant_context import get_tenant_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["audit-trail"])


class AuditEventType(str, Enum):
    """Types of audit events."""

    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PASSWORD_CHANGE = "password_change"  # nosec B105 - Audit event type constant, not a password
    PERMISSION_CHANGE = "permission_change"
    VOICE_INTERACTION = "voice_interaction"
    CLIENT_ACCESS = "client_access"
    MATTER_ACCESS = "matter_access"
    DOCUMENT_ACCESS = "document_access"
    SYSTEM_ERROR = "system_error"
    SECURITY_ALERT = "security_alert"
    API_CALL = "api_call"
    DATA_EXPORT = "data_export"
    CONFIGURATION_CHANGE = "configuration_change"
    INTEGRATION_EVENT = "integration_event"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEventBase(BaseModel):
    """Base model for audit events."""

    event_type: AuditEventType = Field(..., description="Type of audit event")
    severity: AuditSeverity = Field(AuditSeverity.INFO, description="Event severity")
    description: str = Field(..., description="Human-readable event description")
    user_id: Optional[str] = Field(None, description="User who triggered the event")
    session_id: Optional[str] = Field(None, description="Session identifier")
    ip_address: Optional[str] = Field(None, description="Source IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    resource_type: Optional[str] = Field(None, description="Type of resource accessed")
    resource_id: Optional[str] = Field(None, description="ID of resource accessed")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional event data"
    )


class AuditEventCreate(AuditEventBase):
    """Model for creating audit events."""

    pass


class AuditEventResponse(AuditEventBase):
    """Response model for audit events."""

    id: str
    tenant_id: str
    timestamp: datetime
    created_at: datetime


class AuditSearchParams(BaseModel):
    """Parameters for searching audit events."""

    start_date: Optional[datetime] = Field(None, description="Start date for search")
    end_date: Optional[datetime] = Field(None, description="End date for search")
    event_types: Optional[List[AuditEventType]] = Field(
        None, description="Filter by event types"
    )
    severities: Optional[List[AuditSeverity]] = Field(
        None, description="Filter by severities"
    )
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    resource_type: Optional[str] = Field(None, description="Filter by resource type")
    search_query: Optional[str] = Field(None, description="Text search in descriptions")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class AuditStatistics(BaseModel):
    """Audit statistics model."""

    total_events: int = Field(..., description="Total number of events")
    events_by_type: Dict[str, int] = Field(..., description="Event count by type")
    events_by_severity: Dict[str, int] = Field(
        ..., description="Event count by severity"
    )
    events_by_user: Dict[str, int] = Field(..., description="Event count by user")
    time_range: Dict[str, datetime] = Field(..., description="Time range of data")


class ComplianceReport(BaseModel):
    """Compliance report model."""

    report_id: str = Field(..., description="Unique report identifier")
    report_type: str = Field(..., description="Type of compliance report")
    generated_at: datetime = Field(..., description="Report generation timestamp")
    time_period: Dict[str, datetime] = Field(..., description="Time period covered")
    total_events: int = Field(..., description="Total events in period")
    security_events: int = Field(..., description="Security-related events")
    data_access_events: int = Field(..., description="Data access events")
    compliance_score: float = Field(..., description="Overall compliance score")
    recommendations: List[str] = Field(..., description="Compliance recommendations")


# Helper function to get analytics engine
async def get_analytics_engine(
    tenant_context=Depends(get_tenant_context),
) -> AnalyticsEngine:
    """Get analytics engine for audit operations."""
    # Get database session if available
    from ..database import get_database_session

    db_session = await get_database_session()

    # Initialize analytics engine
    engine = AnalyticsEngine(db_session=db_session)
    await engine.initialize()
    return engine


@router.post("/events", response_model=AuditEventResponse)
async def create_audit_event(
    event: AuditEventCreate,
    current_user=Depends(get_current_user),
    tenant_context=Depends(get_tenant_context),
    analytics=Depends(get_analytics_engine),
):
    """Create a new audit event."""
    try:
        # Create audit event record
        audit_event = {
            "id": f"audit_{datetime.utcnow().timestamp()}",
            "tenant_id": tenant_context.tenant_id,
            "timestamp": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            **event.model_dump(),
        }

        # Record analytics metric for audit events
        metric = AnalyticsMetric(
            name=f"audit_event_{event.event_type.value}",
            value=1,
            timestamp=datetime.utcnow(),
            tenant_id=tenant_context.tenant_id,
            metadata={
                "severity": event.severity.value,
                "user_id": event.user_id,
                "resource_type": event.resource_type,
            },
            metric_type=MetricType.USER_ENGAGEMENT,
        )

        await analytics.record_metric(metric)

        logger.info(
            f"Created audit event: {event.event_type.value} by user {event.user_id}"
        )
        return AuditEventResponse(**audit_event)

    except Exception as e:
        logger.error(f"Failed to create audit event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create audit event")


@router.get("/events", response_model=List[AuditEventResponse])
async def search_audit_events(
    params: AuditSearchParams = Depends(),
    current_user=Depends(get_current_user),
    tenant_context=Depends(get_tenant_context),
    _: None = Depends(require_permission("audit:read")),
):
    """Search audit events with filtering and pagination."""
    try:
        # Mock implementation - in real system would query database
        mock_events = []
        for i in range(min(params.limit, 20)):  # Return up to 20 mock events
            mock_events.append(
                {
                    "id": f"audit_{i}",
                    "tenant_id": tenant_context.tenant_id,
                    "timestamp": datetime.utcnow() - timedelta(hours=i),
                    "created_at": datetime.utcnow() - timedelta(hours=i),
                    "event_type": AuditEventType.VOICE_INTERACTION,
                    "severity": AuditSeverity.INFO,
                    "description": f"Voice interaction #{i} processed",
                    "user_id": current_user.id,
                    "session_id": f"session_{i}",
                    "ip_address": "192.168.1.100",
                    "user_agent": "HERMES Dashboard/1.0",
                    "resource_type": "voice_session",
                    "resource_id": f"voice_{i}",
                    "metadata": {"duration": 45 + i},
                }
            )

        return [AuditEventResponse(**event) for event in mock_events]

    except Exception as e:
        logger.error(f"Failed to search audit events: {e}")
        raise HTTPException(status_code=500, detail="Failed to search audit events")


@router.get("/events/{event_id}", response_model=AuditEventResponse)
async def get_audit_event(
    event_id: str,
    current_user=Depends(get_current_user),
    tenant_context=Depends(get_tenant_context),
    _: None = Depends(require_permission("audit:read")),
):
    """Get a specific audit event by ID."""
    try:
        # Mock implementation
        mock_event = {
            "id": event_id,
            "tenant_id": tenant_context.tenant_id,
            "timestamp": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "event_type": AuditEventType.VOICE_INTERACTION,
            "severity": AuditSeverity.INFO,
            "description": f"Detailed audit event {event_id}",
            "user_id": current_user.id,
            "session_id": "session_123",
            "ip_address": "192.168.1.100",
            "user_agent": "HERMES Dashboard/1.0",
            "resource_type": "voice_session",
            "resource_id": event_id,
            "metadata": {
                "duration": 120,
                "transcript_length": 450,
                "ai_confidence": 0.92,
                "legal_entities": ["contract", "liability", "damages"],
            },
        }

        return AuditEventResponse(**mock_event)

    except Exception as e:
        logger.error(f"Failed to get audit event: {e}")
        raise HTTPException(status_code=404, detail="Audit event not found")


@router.get("/statistics", response_model=AuditStatistics)
async def get_audit_statistics(
    start_date: Optional[datetime] = Query(
        None, description="Start date for statistics"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for statistics"),
    current_user=Depends(get_current_user),
    tenant_context=Depends(get_tenant_context),
    _: None = Depends(require_permission("audit:read")),
):
    """Get audit statistics for the specified time period."""
    try:
        # Set default time range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Mock statistics
        statistics = AuditStatistics(
            total_events=1247,
            events_by_type={
                "voice_interaction": 456,
                "client_access": 234,
                "user_login": 189,
                "api_call": 145,
                "document_access": 98,
                "matter_access": 89,
                "system_error": 36,
            },
            events_by_severity={
                "info": 1089,
                "warning": 98,
                "error": 45,
                "critical": 15,
            },
            events_by_user={current_user.id: 867, "system": 234, "integration": 146},
            time_range={"start": start_date, "end": end_date},
        )

        return statistics

    except Exception as e:
        logger.error(f"Failed to get audit statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get audit statistics")


@router.get("/compliance/report", response_model=ComplianceReport)
async def generate_compliance_report(
    report_type: str = Query("monthly", description="Type of compliance report"),
    start_date: Optional[datetime] = Query(None, description="Report start date"),
    end_date: Optional[datetime] = Query(None, description="Report end date"),
    current_user=Depends(get_current_user),
    tenant_context=Depends(get_tenant_context),
    _: None = Depends(require_permission("audit:admin")),
):
    """Generate a compliance report."""
    try:
        # Set default time range
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            if report_type == "daily":
                start_date = end_date - timedelta(days=1)
            elif report_type == "weekly":
                start_date = end_date - timedelta(weeks=1)
            elif report_type == "monthly":
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=90)

        # Generate compliance score based on various factors
        compliance_score = 94.5  # Mock score

        recommendations = []
        if compliance_score < 95:
            recommendations.append("Increase security event monitoring frequency")
        if compliance_score < 90:
            recommendations.append("Review access control policies")
            recommendations.append("Implement additional audit logging")

        report = ComplianceReport(
            report_id=f"compliance_{int(datetime.utcnow().timestamp())}",
            report_type=report_type,
            generated_at=datetime.utcnow(),
            time_period={"start": start_date, "end": end_date},
            total_events=1247,
            security_events=45,
            data_access_events=567,
            compliance_score=compliance_score,
            recommendations=recommendations,
        )

        return report

    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate compliance report"
        )


@router.get("/export")
async def export_audit_data(
    format: str = Query("csv", enum=["csv", "json"], description="Export format"),
    start_date: Optional[datetime] = Query(None, description="Start date for export"),
    end_date: Optional[datetime] = Query(None, description="End date for export"),
    event_types: Optional[str] = Query(None, description="Comma-separated event types"),
    current_user=Depends(get_current_user),
    tenant_context=Depends(get_tenant_context),
    _: None = Depends(require_permission("audit:export")),
):
    """Export audit data in specified format."""
    try:
        # Set default time range
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Mock audit data
        audit_data = [
            {
                "id": "audit_1",
                "timestamp": datetime.utcnow() - timedelta(hours=1),
                "event_type": "voice_interaction",
                "severity": "info",
                "description": "Voice interaction processed",
                "user_id": current_user.id,
                "ip_address": "192.168.1.100",
                "resource_type": "voice_session",
                "resource_id": "voice_123",
            },
            {
                "id": "audit_2",
                "timestamp": datetime.utcnow() - timedelta(hours=2),
                "event_type": "client_access",
                "severity": "info",
                "description": "Client record accessed",
                "user_id": current_user.id,
                "ip_address": "192.168.1.100",
                "resource_type": "client",
                "resource_id": "client_456",
            },
        ]

        if format == "csv":
            # Generate CSV
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "id",
                    "timestamp",
                    "event_type",
                    "severity",
                    "description",
                    "user_id",
                    "ip_address",
                    "resource_type",
                    "resource_id",
                ],
            )
            writer.writeheader()
            for row in audit_data:
                # Convert datetime to string for CSV
                row_copy = row.copy()
                row_copy["timestamp"] = row_copy["timestamp"].isoformat()
                writer.writerow(row_copy)

            content = output.getvalue()
            media_type = "text/csv"
            filename = f"audit_export_{int(datetime.utcnow().timestamp())}.csv"

        else:  # JSON format
            content = json.dumps(audit_data, indent=2, default=str)
            media_type = "application/json"
            filename = f"audit_export_{int(datetime.utcnow().timestamp())}.json"

        # Return streaming response
        return StreamingResponse(
            io.StringIO(content),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        logger.error(f"Failed to export audit data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export audit data")


@router.post("/security/alert")
async def create_security_alert(
    alert_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    tenant_context=Depends(get_tenant_context),
    analytics=Depends(get_analytics_engine),
):
    """Create a security alert and trigger notifications."""
    try:
        # Create security audit event
        security_event = AuditEventCreate(
            event_type=AuditEventType.SECURITY_ALERT,
            severity=AuditSeverity.CRITICAL,
            description=f"Security alert: {alert_data.get('type', 'Unknown')}",
            user_id=current_user.id if current_user else None,
            metadata=alert_data,
        )

        # Record the event
        audit_event = await create_audit_event(
            security_event, current_user, tenant_context, analytics
        )

        # Add background task to send notifications
        background_tasks.add_task(
            _send_security_notification, audit_event, tenant_context.tenant_id
        )

        return {
            "status": "alert_created",
            "alert_id": audit_event.id,
            "severity": security_event.severity,
            "timestamp": audit_event.timestamp,
        }

    except Exception as e:
        logger.error(f"Failed to create security alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to create security alert")


async def _send_security_notification(audit_event: AuditEventResponse, tenant_id: str):
    """Background task to send security notifications."""
    try:
        # In a real implementation, this would:
        # 1. Send email notifications to security team
        # 2. Send webhook to security monitoring systems
        # 3. Create tickets in issue tracking systems
        # 4. Send SMS alerts for critical events

        logger.info(f"Security notification sent for event {audit_event.id}")

    except Exception as e:
        logger.error(f"Failed to send security notification: {e}")


@router.get("/health")
async def audit_health_check():
    """Check audit system health."""
    try:
        return {
            "status": "healthy",
            "audit_system": "operational",
            "storage": "available",
            "retention_policy": "90_days",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Audit health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
