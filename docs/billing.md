# Billing and Subscription Operations

HERMES uses Stripe for subscription management and usage metering.

## Environment Variables
- `STRIPE_API_KEY`: secret API key for Stripe
- `STRIPE_WEBHOOK_SECRET`: signing secret for webhook verification
- `STRIPE_PRICE_PRO`: price ID for Professional plan
- `STRIPE_PRICE_ENTERPRISE`: price ID for Enterprise plan
- `STRIPE_OVERAGE_PRICE`: price ID for per-interaction overage

## Webhook Setup
Configure a Stripe webhook endpoint pointing to `/api/billing/webhook`.
Include events for:
- `invoice.paid`
- `invoice.payment_failed`
- `customer.subscription.deleted`

## Usage Recording
Each voice interaction is reported to Stripe using usage records. Overages on the Professional tier are billed at $1.00 per extra interaction beyond 2,000 per month.

## Customer Portal
Clients can manage billing through the Stripe customer portal. Use the `/api/billing/portal` endpoint to generate a session URL.
