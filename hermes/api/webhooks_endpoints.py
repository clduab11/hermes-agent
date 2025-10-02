"""
Webhooks API endpoints for HERMES Marketing Command Center
Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.

Provides Zapier integration webhook endpoints.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_database_session
from ..database.models import WebhookEvent
from ..database.tenant_context import get_tenant_context
from ..services.zapier_service import ZapierService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


class WebhookPayload(BaseModel):
    """Webhook payload model."""
    event_type: str
    source: str = "zapier"
    data: Dict[str, Any]


class WebhookResponse(BaseModel):
    """Webhook response model."""
    id: int
    event_type: str
    source: str
    processed: bool
    error_message: str = None

    class Config:
        from_attributes = True


@router.post("/incoming", response_model=WebhookResponse, status_code=202)
async def receive_webhook(
    payload: WebhookPayload,
    db: Session = Depends(get_database_session),
    tenant_context=Depends(get_tenant_context),
):
    """Receive incoming webhook from Zapier or other integrations.
    
    This endpoint accepts webhook payloads and queues them for processing.
    The actual processing happens asynchronously to ensure fast response times.
    """
    try:
        service = ZapierService(db)
        tenant_id = tenant_context.get("tenant_id") if tenant_context else None
        
        event = await service.process_incoming_webhook(
            event_type=payload.event_type,
            source=payload.source,
            payload=payload.data,
            tenant_id=tenant_id
        )
        
        await service.cleanup()
        
        return event
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process webhook")


@router.post("/trigger")
async def trigger_webhook(
    webhook_url: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_database_session),
):
    """Trigger an outgoing webhook to Zapier.
    
    This endpoint allows the system to push data to Zapier workflows.
    """
    try:
        service = ZapierService(db)
        
        success = await service.trigger_zap(webhook_url, payload)
        
        await service.cleanup()
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to trigger webhook")
        
        return {"status": "success", "message": "Webhook triggered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to trigger webhook")


@router.get("/events", response_model=List[WebhookResponse])
async def list_events(
    limit: int = 100,
    processed: bool = None,
    db: Session = Depends(get_database_session),
    tenant_context=Depends(get_tenant_context),
):
    """List webhook events with optional filtering."""
    try:
        query = db.query(WebhookEvent)
        
        if tenant_context:
            tenant_id = tenant_context.get("tenant_id")
            if tenant_id:
                query = query.filter(WebhookEvent.tenant_id == tenant_id)
        
        if processed is not None:
            query = query.filter(WebhookEvent.processed == processed)
        
        events = query.order_by(WebhookEvent.created_at.desc()).limit(limit).all()
        
        return events
        
    except Exception as e:
        logger.error(f"Error listing webhook events: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve webhook events")


@router.get("/events/{event_id}", response_model=WebhookResponse)
async def get_event(
    event_id: int,
    db: Session = Depends(get_database_session),
    tenant_context=Depends(get_tenant_context),
):
    """Get a specific webhook event."""
    try:
        query = db.query(WebhookEvent).filter(WebhookEvent.id == event_id)
        
        if tenant_context:
            tenant_id = tenant_context.get("tenant_id")
            if tenant_id:
                query = query.filter(WebhookEvent.tenant_id == tenant_id)
        
        event = query.first()
        
        if not event:
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
        
        return event
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving webhook event {event_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve webhook event")
