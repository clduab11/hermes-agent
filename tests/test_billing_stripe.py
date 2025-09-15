from unittest.mock import MagicMock, patch

import pytest
import stripe

from hermes.billing import StripeBillingService, SubscriptionTier


@pytest.fixture
def service():
    return StripeBillingService(api_key="sk_test", webhook_secret="whsec_test")


def test_create_customer(service):
    with patch.object(
        stripe.Customer, "create", return_value=MagicMock(id="cus_123")
    ) as mock_create:
        customer = service.create_customer("tenant1", "user@example.com")
        assert customer.id == "cus_123"
        mock_create.assert_called_once()


def test_create_subscription(service):
    service.price_map[SubscriptionTier.PROFESSIONAL] = "price_pro"
    with patch.object(
        stripe.Subscription, "create", return_value=MagicMock(id="sub_123")
    ) as mock_create:
        subscription = service.create_subscription(
            "cus_123", SubscriptionTier.PROFESSIONAL
        )
        assert subscription.id == "sub_123"
        mock_create.assert_called_once()


def test_record_interaction(service):
    mock_subscription = MagicMock()
    mock_subscription.data = [MagicMock(items=MagicMock(data=[MagicMock(id="si_123")]))]
    if not hasattr(stripe, "UsageRecord"):
        stripe.UsageRecord = MagicMock()
    with (
        patch.object(
            stripe.Subscription, "list", return_value=mock_subscription
        ) as list_call,
        patch.object(
            stripe.UsageRecord, "create", return_value=MagicMock()
        ) as usage_call,
    ):
        service.record_interaction("tenant1")
        list_call.assert_called_once()
        usage_call.assert_called_once()


def test_calculate_overage_cost():
    assert (
        StripeBillingService.calculate_overage_cost(2500, SubscriptionTier.PROFESSIONAL)
        == 500.0
    )
    assert (
        StripeBillingService.calculate_overage_cost(1000, SubscriptionTier.PROFESSIONAL)
        == 0.0
    )
    assert (
        StripeBillingService.calculate_overage_cost(5000, SubscriptionTier.ENTERPRISE)
        == 0.0
    )


def test_handle_webhook(service):
    event = {"type": "invoice.paid", "data": {"object": {"customer": "cus_123"}}}
    with patch.object(
        stripe.Webhook, "construct_event", return_value=event
    ) as mock_construct:
        service.handle_webhook(b"payload", "sig")
        mock_construct.assert_called_once()
