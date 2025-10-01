"""
Zapier Webhooks - REST Hooks Implementation
September 2025 best practices for webhook delivery
"""

import hashlib
import hmac
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx

from ...resilience.retry import retry_async
from .models import EventType, WebhookEvent, WebhookSubscription

logger = logging.getLogger(__name__)


class ZapierWebhooks:
    """
    Zapier webhook manager for HERMES events.
    
    Implements REST Hooks pattern for instant notifications to Zapier.
    """

    def __init__(
        self,
        secret_key: str,
        timeout: float = 10.0,
    ):
        """
        Initialize webhook manager.
        
        Args:
            secret_key: Secret for signing webhook payloads
            timeout: Request timeout for webhook delivery
        """
        self.secret_key = secret_key
        self.timeout = timeout
        self._subscriptions: Dict[str, WebhookSubscription] = {}
        self._client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> None:
        """Initialize HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
            logger.info("Zapier webhooks initialized")

    async def close(self) -> None:
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None

    def subscribe(
        self,
        target_url: str,
        event_type: EventType,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WebhookSubscription:
        """
        Subscribe to webhook events.
        
        Args:
            target_url: URL to send webhooks to
            event_type: Type of event to subscribe to
            metadata: Optional metadata
            
        Returns:
            Subscription details
        """
        subscription = WebhookSubscription(
            subscription_id=str(uuid4()),
            target_url=target_url,
            event_type=event_type,
            created_at=datetime.utcnow(),
            metadata=metadata or {},
        )
        
        self._subscriptions[subscription.subscription_id] = subscription
        logger.info(f"Created webhook subscription: {subscription.subscription_id} for {event_type.value}")
        
        return subscription

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from webhook events.
        
        Args:
            subscription_id: Subscription to remove
            
        Returns:
            True if successful
        """
        if subscription_id in self._subscriptions:
            del self._subscriptions[subscription_id]
            logger.info(f"Removed webhook subscription: {subscription_id}")
            return True
        return False

    def list_subscriptions(
        self,
        event_type: Optional[EventType] = None,
    ) -> List[WebhookSubscription]:
        """
        List webhook subscriptions.
        
        Args:
            event_type: Filter by event type
            
        Returns:
            List of subscriptions
        """
        subscriptions = list(self._subscriptions.values())
        
        if event_type:
            subscriptions = [s for s in subscriptions if s.event_type == event_type]
        
        return subscriptions

    def _sign_payload(self, payload: str) -> str:
        """
        Create HMAC signature for webhook payload.
        
        Args:
            payload: JSON string payload
            
        Returns:
            HMAC signature
        """
        signature = hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature

    @retry_async(max_attempts=3, initial_delay=1.0)
    async def _deliver_webhook(
        self,
        subscription: WebhookSubscription,
        event: WebhookEvent,
    ) -> bool:
        """
        Deliver webhook to subscribed URL.
        
        Args:
            subscription: Target subscription
            event: Event to deliver
            
        Returns:
            True if successful
        """
        if not self._client:
            await self.initialize()

        # Prepare payload
        payload = event.model_dump_json()
        signature = self._sign_payload(payload)
        
        headers = {
            "Content-Type": "application/json",
            "X-Hermes-Signature": signature,
            "X-Hermes-Event": event.event_type.value,
            "X-Hermes-Event-ID": event.event_id,
        }
        
        try:
            response = await self._client.post(
                str(subscription.target_url),
                content=payload,
                headers=headers,
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(
                    f"Webhook delivered successfully: {event.event_id} -> "
                    f"{subscription.target_url}"
                )
                
                # Update subscription
                subscription.last_triggered_at = datetime.utcnow()
                return True
            else:
                logger.warning(
                    f"Webhook delivery failed: {response.status_code} -> "
                    f"{subscription.target_url}"
                )
                return False
                
        except Exception as e:
            logger.error(f"Webhook delivery error: {e}")
            raise

    async def trigger_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Trigger webhook event for all subscribers.
        
        Args:
            event_type: Type of event
            data: Event data
            metadata: Optional metadata
            
        Returns:
            Number of successful deliveries
        """
        event = WebhookEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            data=data,
            metadata=metadata or {},
        )
        
        # Find subscriptions for this event type
        subscriptions = [
            s for s in self._subscriptions.values()
            if s.event_type == event_type and s.active
        ]
        
        if not subscriptions:
            logger.info(f"No subscribers for event: {event_type.value}")
            return 0
        
        logger.info(
            f"Triggering event {event_type.value} for {len(subscriptions)} subscribers"
        )
        
        # Deliver webhooks concurrently
        import asyncio
        tasks = [
            self._deliver_webhook(subscription, event)
            for subscription in subscriptions
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful deliveries
        successful = sum(1 for r in results if r is True)
        
        logger.info(
            f"Event {event.event_id}: {successful}/{len(subscriptions)} deliveries successful"
        )
        
        return successful

    # Convenience methods for common events

    async def trigger_matter_created(
        self,
        matter_id: str,
        client_name: str,
        matter_type: str,
        **kwargs
    ) -> int:
        """Trigger matter.created event"""
        data = {
            "matter_id": matter_id,
            "client_name": client_name,
            "matter_type": matter_type,
            **kwargs
        }
        return await self.trigger_event(EventType.MATTER_CREATED, data)

    async def trigger_client_contacted(
        self,
        client_name: str,
        contact_method: str,
        **kwargs
    ) -> int:
        """Trigger client.contacted event"""
        data = {
            "client_name": client_name,
            "contact_method": contact_method,
            **kwargs
        }
        return await self.trigger_event(EventType.CLIENT_CONTACTED, data)

    async def trigger_intake_completed(
        self,
        intake_id: str,
        client_name: str,
        matter_type: str,
        **kwargs
    ) -> int:
        """Trigger intake.completed event"""
        data = {
            "intake_id": intake_id,
            "client_name": client_name,
            "matter_type": matter_type,
            **kwargs
        }
        return await self.trigger_event(EventType.INTAKE_COMPLETED, data)

    async def trigger_payment_received(
        self,
        payment_id: str,
        amount: float,
        client_name: str,
        **kwargs
    ) -> int:
        """Trigger payment.received event"""
        data = {
            "payment_id": payment_id,
            "amount": amount,
            "client_name": client_name,
            **kwargs
        }
        return await self.trigger_event(EventType.PAYMENT_RECEIVED, data)
