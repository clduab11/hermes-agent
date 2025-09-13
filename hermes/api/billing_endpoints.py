"""Stripe billing API endpoints for subscription management."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

from ..auth.middleware import get_current_user, require_permission
from ..billing import StripeBillingService, SubscriptionTier
from ..database.tenant_context import get_tenant_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])


class SubscriptionRequest(BaseModel):
    """Request body for creating a subscription."""

    tier: SubscriptionTier
    email: EmailStr
    trial_period_days: Optional[int] = None


@router.post("/subscribe")
async def create_subscription(
    request: SubscriptionRequest,
    current_user=Depends(get_current_user),
    tenant_context=Depends(get_tenant_context),
    _: None = Depends(require_permission("billing:manage")),
):
    """Create a Stripe subscription for the current tenant."""
    try:
        service = StripeBillingService()
        customer = service.create_customer(
            tenant_id=tenant_context.tenant_id,
            email=request.email,
        )
        subscription = service.create_subscription(
            customer_id=customer.id,
            tier=request.tier,
            trial_period_days=request.trial_period_days,
        )
        return {"subscription_id": subscription.id}
    except Exception as exc:  # pragma: no cover - logged for audit
        logger.error(f"Failed to create subscription: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Subscription failed"
        )


@router.post("/portal")
async def create_portal_session(
    return_url: str,
    current_user=Depends(get_current_user),
    tenant_context=Depends(get_tenant_context),
    _: None = Depends(require_permission("billing:manage")),
):
    """Generate a billing portal session for self-service management."""
    try:
        service = StripeBillingService()
        customer = service.create_customer(
            tenant_id=tenant_context.tenant_id,
            email=current_user.email,
        )
        url = service.create_portal_session(customer.id, return_url)
        return {"url": url}
    except Exception as exc:  # pragma: no cover
        logger.error(f"Failed to create portal session: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Portal session failed"
        )


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request):
    """Stripe webhook endpoint."""
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        service = StripeBillingService()
        service.handle_webhook(payload, signature)
    except Exception as exc:  # pragma: no cover
        logger.error(f"Webhook error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook handling failed"
        )
    return {"status": "success"}
