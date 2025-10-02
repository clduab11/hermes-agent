"""
Zapier Service for HERMES Marketing Command Center
Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.

Handles webhook processing and triggering for Zapier integration.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from ..database.models import WebhookEvent

logger = logging.getLogger(__name__)


class ZapierService:
    """Service for processing Zapier webhooks and triggers."""
    
    def __init__(self, db_session: Session):
        """Initialize Zapier service.
        
        Args:
            db_session: Database session for webhook event logging
        """
        self.db = db_session
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def process_incoming_webhook(
        self,
        event_type: str,
        source: str,
        payload: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> WebhookEvent:
        """Process incoming webhook from Zapier.
        
        Args:
            event_type: Type of event (e.g., "lead.created", "post.scheduled")
            source: Source of webhook (e.g., "zapier", "clio")
            payload: Webhook payload data
            tenant_id: Tenant ID for multi-tenant isolation
            
        Returns:
            WebhookEvent object with processing status
        """
        try:
            # Create webhook event record
            event = WebhookEvent(
                event_type=event_type,
                source=source,
                payload=payload,
                tenant_id=tenant_id,
                processed=False
            )
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            
            # Process event based on type
            if event_type.startswith("lead."):
                await self._process_lead_event(event)
            elif event_type.startswith("social."):
                await self._process_social_event(event)
            
            # Mark as processed
            event.processed = True
            event.processed_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Processed webhook event {event.id}: {event_type}")
            return event
            
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            if event:
                event.error_message = str(e)
                event.retry_count += 1
                self.db.commit()
            raise
    
    async def trigger_zap(
        self,
        webhook_url: str,
        payload: Dict[str, Any]
    ) -> bool:
        """Trigger a Zapier webhook.
        
        Args:
            webhook_url: Zapier webhook URL
            payload: Data to send to Zapier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = await self.client.post(webhook_url, json=payload)
            response.raise_for_status()
            logger.info(f"Triggered Zapier webhook: {webhook_url}")
            return True
        except Exception as e:
            logger.error(f"Error triggering Zapier webhook: {str(e)}")
            return False
    
    async def _process_lead_event(self, event: WebhookEvent) -> None:
        """Process lead-related webhook event."""
        # Implementation for lead event processing
        logger.info(f"Processing lead event: {event.event_type}")
    
    async def _process_social_event(self, event: WebhookEvent) -> None:
        """Process social media-related webhook event."""
        # Implementation for social event processing
        logger.info(f"Processing social event: {event.event_type}")
    
    async def get_unprocessed_events(
        self,
        limit: int = 100,
        tenant_id: Optional[str] = None
    ) -> List[WebhookEvent]:
        """Get unprocessed webhook events.
        
        Args:
            limit: Maximum number of events to return
            tenant_id: Filter by tenant ID
            
        Returns:
            List of unprocessed WebhookEvent objects
        """
        query = self.db.query(WebhookEvent).filter(
            WebhookEvent.processed == False,
            WebhookEvent.retry_count < WebhookEvent.max_retries
        )
        
        if tenant_id:
            query = query.filter(WebhookEvent.tenant_id == tenant_id)
        
        return query.order_by(WebhookEvent.created_at).limit(limit).all()
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self.client.aclose()
