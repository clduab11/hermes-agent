"""
Test Zapier webhooks integration
"""

import os
os.environ["OPENAI_API_KEY"] = "test-key-123"
os.environ["DEBUG"] = "true"

import pytest
from unittest.mock import AsyncMock, Mock, patch
import hashlib
import hmac

from hermes.integrations.zapier.webhooks import ZapierWebhooks
from hermes.integrations.zapier.models import EventType, WebhookEvent, WebhookSubscription


class TestZapierWebhooks:
    """Test Zapier webhook manager"""

    @pytest.mark.asyncio
    async def test_webhooks_initialization(self):
        """Test webhooks can be initialized"""
        webhooks = ZapierWebhooks(secret_key="test-secret")
        await webhooks.initialize()
        
        assert webhooks._client is not None
        await webhooks.close()

    def test_subscribe(self):
        """Test webhook subscription"""
        webhooks = ZapierWebhooks(secret_key="test-secret")
        
        subscription = webhooks.subscribe(
            target_url="https://example.com/webhook",
            event_type=EventType.MATTER_CREATED
        )
        
        assert subscription.subscription_id is not None
        assert subscription.event_type == EventType.MATTER_CREATED
        assert subscription.active is True

    def test_unsubscribe(self):
        """Test webhook unsubscription"""
        webhooks = ZapierWebhooks(secret_key="test-secret")
        
        subscription = webhooks.subscribe(
            target_url="https://example.com/webhook",
            event_type=EventType.MATTER_CREATED
        )
        
        assert webhooks.unsubscribe(subscription.subscription_id) is True
        assert webhooks.unsubscribe("non-existent") is False

    def test_list_subscriptions(self):
        """Test listing subscriptions"""
        webhooks = ZapierWebhooks(secret_key="test-secret")
        
        webhooks.subscribe(
            target_url="https://example.com/webhook1",
            event_type=EventType.MATTER_CREATED
        )
        webhooks.subscribe(
            target_url="https://example.com/webhook2",
            event_type=EventType.CLIENT_CONTACTED
        )
        
        all_subs = webhooks.list_subscriptions()
        assert len(all_subs) == 2
        
        matter_subs = webhooks.list_subscriptions(event_type=EventType.MATTER_CREATED)
        assert len(matter_subs) == 1

    def test_sign_payload(self):
        """Test payload signing"""
        webhooks = ZapierWebhooks(secret_key="test-secret")
        
        payload = '{"test": "data"}'
        signature = webhooks._sign_payload(payload)
        
        # Verify signature is correct
        expected = hmac.new(
            "test-secret".encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        assert signature == expected

    @pytest.mark.asyncio
    async def test_deliver_webhook(self):
        """Test webhook delivery"""
        webhooks = ZapierWebhooks(secret_key="test-secret")
        await webhooks.initialize()
        
        subscription = WebhookSubscription(
            target_url="https://example.com/webhook",
            event_type=EventType.MATTER_CREATED
        )
        
        event = WebhookEvent(
            event_id="event_123",
            event_type=EventType.MATTER_CREATED,
            data={"matter_id": "matter_1"}
        )
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch.object(webhooks._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            success = await webhooks._deliver_webhook(subscription, event)
            
            assert success is True
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_event(self):
        """Test triggering webhook event"""
        webhooks = ZapierWebhooks(secret_key="test-secret")
        await webhooks.initialize()
        
        # Subscribe to event
        webhooks.subscribe(
            target_url="https://example.com/webhook",
            event_type=EventType.MATTER_CREATED
        )
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch.object(webhooks._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            count = await webhooks.trigger_event(
                event_type=EventType.MATTER_CREATED,
                data={"matter_id": "matter_1"}
            )
            
            assert count == 1

    @pytest.mark.asyncio
    async def test_trigger_matter_created(self):
        """Test convenience method for matter.created"""
        webhooks = ZapierWebhooks(secret_key="test-secret")
        await webhooks.initialize()
        
        webhooks.subscribe(
            target_url="https://example.com/webhook",
            event_type=EventType.MATTER_CREATED
        )
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch.object(webhooks._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            count = await webhooks.trigger_matter_created(
                matter_id="matter_123",
                client_name="John Doe",
                matter_type="Personal Injury"
            )
            
            assert count == 1


class TestWebhookModels:
    """Test webhook data models"""

    def test_webhook_subscription_validation(self):
        """Test WebhookSubscription validation"""
        subscription = WebhookSubscription(
            target_url="https://example.com/webhook",
            event_type=EventType.MATTER_CREATED
        )
        
        assert subscription.active is True
        assert str(subscription.target_url) == "https://example.com/webhook"

    def test_webhook_event_validation(self):
        """Test WebhookEvent validation"""
        event = WebhookEvent(
            event_id="event_123",
            event_type=EventType.CLIENT_CONTACTED,
            data={"client": "John Doe"}
        )
        
        assert event.event_id == "event_123"
        assert event.data["client"] == "John Doe"

    def test_event_type_enum(self):
        """Test EventType enum"""
        assert EventType.MATTER_CREATED.value == "matter.created"
        assert EventType.CLIENT_CONTACTED.value == "client.contacted"
        assert EventType.PAYMENT_RECEIVED.value == "payment.received"
