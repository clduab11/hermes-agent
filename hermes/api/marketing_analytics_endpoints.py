"""
Marketing Analytics API endpoints for HERMES Marketing Command Center
Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.

Provides marketing metrics and funnel data endpoints.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_database_session
from ..database.tenant_context import get_tenant_context
from ..services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/marketing/analytics", tags=["marketing_analytics"])


class MetricsResponse(BaseModel):
    """Metrics response model."""
    funnel: Dict[str, Any]
    pipeline: Dict[str, Any]
    social: Dict[str, Any]
    roi: Dict[str, Any]
    generated_at: str


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    db: Session = Depends(get_database_session),
    tenant_context=Depends(get_tenant_context),
):
    """Get comprehensive marketing metrics."""
    try:
        service = AnalyticsService(db)
        tenant_id = tenant_context.get("tenant_id") if tenant_context else None
        
        metrics = await service.get_dashboard_metrics(tenant_id=tenant_id)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error retrieving metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/funnel")
async def get_funnel(
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    db: Session = Depends(get_database_session),
    tenant_context=Depends(get_tenant_context),
):
    """Get conversion funnel metrics."""
    try:
        service = AnalyticsService(db)
        tenant_id = tenant_context.get("tenant_id") if tenant_context else None
        
        funnel = await service.get_funnel_metrics(tenant_id=tenant_id, days=days)
        
        return funnel
        
    except Exception as e:
        logger.error(f"Error retrieving funnel metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline")
async def get_pipeline(
    db: Session = Depends(get_database_session),
    tenant_context=Depends(get_tenant_context),
):
    """Get pipeline value metrics."""
    try:
        service = AnalyticsService(db)
        tenant_id = tenant_context.get("tenant_id") if tenant_context else None
        
        pipeline = await service.get_pipeline_value(tenant_id=tenant_id)
        
        return pipeline
        
    except Exception as e:
        logger.error(f"Error retrieving pipeline metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/social")
async def get_social_performance(
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    db: Session = Depends(get_database_session),
    tenant_context=Depends(get_tenant_context),
):
    """Get social media performance metrics."""
    try:
        service = AnalyticsService(db)
        tenant_id = tenant_context.get("tenant_id") if tenant_context else None
        
        social = await service.get_social_performance(tenant_id=tenant_id, days=days)
        
        return social
        
    except Exception as e:
        logger.error(f"Error retrieving social metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roi")
async def get_roi(
    db: Session = Depends(get_database_session),
    tenant_context=Depends(get_tenant_context),
):
    """Get ROI metrics."""
    try:
        service = AnalyticsService(db)
        tenant_id = tenant_context.get("tenant_id") if tenant_context else None
        
        roi = await service.get_roi_metrics(tenant_id=tenant_id)
        
        return roi
        
    except Exception as e:
        logger.error(f"Error retrieving ROI metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
