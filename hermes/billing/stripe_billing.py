import logging
import uuid
from enum import Enum
from typing import Optional

import stripe

from ..config import settings

logger = logging.getLogger(__name__)


class SubscriptionTier(str, Enum):
    """Subscription tiers available for HERMES."""

    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class StripeBillingService:
    """Service for managing Stripe billing and usage."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or settings.stripe_api_key
        self.webhook_secret = webhook_secret or settings.stripe_webhook_secret
        if not self.api_key:
            raise ValueError("Stripe API key not configured")
        stripe.api_key = self.api_key
        self.price_map = {
            SubscriptionTier.PROFESSIONAL: settings.stripe_price_pro,
            SubscriptionTier.ENTERPRISE: settings.stripe_price_enterprise,
        }

    # ------------------------------------------------------------------
    # Customer and Subscription Management
    # ------------------------------------------------------------------
    def create_customer(self, tenant_id: str, email: str) -> stripe.Customer:
        """Create a Stripe customer for the given tenant."""
        logger.info("Creating Stripe customer", extra={"tenant_id": tenant_id})
        customer = stripe.Customer.create(
            email=email,
            metadata={"tenant_id": tenant_id},
            idempotency_key=str(uuid.uuid4()),
        )
        return customer

    def create_subscription(
        self,
        customer_id: str,
        tier: SubscriptionTier,
        trial_period_days: Optional[int] = None,
    ) -> stripe.Subscription:
        """Create a subscription for the specified tier."""
        price_id = self.price_map.get(tier)
        if not price_id:
            raise ValueError(f"Price ID not configured for tier {tier}")
        trial_days = (
            trial_period_days
            if trial_period_days is not None
            else settings.stripe_trial_days
        )
        logger.info(
            "Creating Stripe subscription",
            extra={"customer_id": customer_id, "tier": tier.value},
        )
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            trial_period_days=trial_days,
            expand=["latest_invoice.payment_intent"],
            idempotency_key=str(uuid.uuid4()),
        )
        return subscription

    # ------------------------------------------------------------------
    # Usage Recording
    # ------------------------------------------------------------------
    def record_interaction(self, tenant_id: str, quantity: int = 1) -> None:
        """Record a voice interaction for usage-based billing."""
        logger.debug(
            "Recording interaction usage",
            extra={"tenant_id": tenant_id, "quantity": quantity},
        )
        subscriptions = stripe.Subscription.list(
            limit=1,
            expand=["data.items"],
            metadata={"tenant_id": tenant_id},
        )
        if not subscriptions.data:
            raise ValueError("Active subscription not found for tenant")
        item_id = subscriptions.data[0].items.data[0].id
        stripe.UsageRecord.create(
            subscription_item=item_id,
            quantity=quantity,
            action="increment",
            idempotency_key=str(uuid.uuid4()),
        )

    # ------------------------------------------------------------------
    # Billing Portal
    # ------------------------------------------------------------------
    def create_portal_session(self, customer_id: str, return_url: str) -> str:
        """Create a customer portal session URL."""
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
            idempotency_key=str(uuid.uuid4()),
        )
        return session.url

    # ------------------------------------------------------------------
    # Usage Cost Calculation
    # ------------------------------------------------------------------
    @staticmethod
    def calculate_overage_cost(interactions: int, tier: SubscriptionTier) -> float:
        """Calculate overage cost for a given number of interactions."""
        if tier == SubscriptionTier.PROFESSIONAL:
            included = 2000
            overage_rate = 1.0  # USD per interaction beyond included amount
            return max(0, interactions - included) * overage_rate
        return 0.0

    # ------------------------------------------------------------------
    # Webhook Handling
    # ------------------------------------------------------------------
    def handle_webhook(self, payload: bytes, signature: str) -> None:
        """Handle incoming Stripe webhook events."""
        if not self.webhook_secret:
            raise ValueError("Webhook secret not configured")
        event = stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})
        logger.info("Stripe webhook received", extra={"event_type": event_type})
        if event_type == "invoice.payment_failed":
            logger.warning("Payment failed", extra={"customer": data.get("customer")})
        elif event_type == "customer.subscription.deleted":
            logger.info(
                "Subscription cancelled", extra={"customer": data.get("customer")}
            )
        elif event_type == "invoice.paid":
            logger.info("Invoice paid", extra={"customer": data.get("customer")})
        # Additional event types can be handled here
