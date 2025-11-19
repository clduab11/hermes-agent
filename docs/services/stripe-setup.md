# Stripe Billing Setup Guide

This guide walks you through setting up Stripe for billing and subscription management in HERMES.

---

## Overview

HERMES uses Stripe for:
- Monthly subscription billing ($2,497/month Enterprise plan)
- Usage-based billing ($0.25 per interaction over limit)
- Customer management and invoicing
- Payment method storage
- Webhook events for automated billing workflows

**Reference Code**: `hermes/billing/stripe_billing.py`

---

## Step 1: Create Stripe Account

1. Go to [stripe.com](https://stripe.com/)
2. Click "Start now" or "Sign up"
3. Enter your business information
4. Verify your email address

---

## Step 2: Activate Your Account

Before going live, you must activate your Stripe account:

1. Go to [dashboard.stripe.com](https://dashboard.stripe.com/)
2. Click "Activate your account" in the top banner
3. Provide required information:
   - **Business details**: Legal name, address, tax ID
   - **Bank account**: For receiving payouts
   - **Identity verification**: Upload ID document
   - **Business verification**: Upload business documents (if applicable)
4. Wait for verification (usually 1-3 business days)

---

## Step 3: Create Products & Pricing

### Create Enterprise Plan Product

1. Go to **Products** → **Add product**
2. Fill in product details:
   - **Name**: `HERMES Enterprise Plan`
   - **Description**: `Comprehensive Legal AI Platform for Modern Law Practices`
   - **Statement descriptor**: `HERMES ENT` (appears on credit card statements)
   - **Unit label**: `month` (optional)
3. Click "Save product"

### Add Pricing for Enterprise Plan

1. In the product page, click "Add price"
2. Configure pricing:
   - **Pricing model**: Standard pricing
   - **Price**: `$2,497.00`
   - **Billing period**: Monthly
   - **Usage type**: Licensed
   - **Tax behavior**: Taxable (or Exclusive if you handle tax separately)
3. Click "Add price"
4. **Copy the Price ID** (starts with `price_...`) - you'll need this for `.env`

### Create Overage Product

1. Go to **Products** → **Add product**
2. Fill in product details:
   - **Name**: `HERMES Interaction Overage`
   - **Description**: `Additional client interactions beyond plan limit`
   - **Statement descriptor**: `HERMES USE`
3. Click "Save product"

### Add Pricing for Overage

1. In the overage product page, click "Add price"
2. Configure pricing:
   - **Pricing model**: Standard pricing
   - **Price**: `$0.25`
   - **Billing period**: Monthly
   - **Usage type**: Metered (important!)
   - **Aggregation**: Sum of usage during period
3. Click "Add price"
4. **Copy the Price ID** (starts with `price_...`)

---

## Step 4: Configure Webhook Endpoint

Webhooks notify HERMES of billing events in real-time.

### Create Webhook

1. Go to **Developers** → **Webhooks**
2. Click "Add endpoint"
3. Configure webhook:
   - **Endpoint URL**: `https://your-app-url.com/api/billing/webhook`
     - For local testing: Use ngrok or similar (see Testing section)
     - For production: Your actual GCP App Engine URL
   - **Description**: `HERMES Billing Webhook`
   - **Events to send**: Select these events:
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.paid`
     - `invoice.payment_failed`
     - `invoice.payment_action_required`
     - `payment_method.attached`
     - `payment_method.detached`
4. Click "Add endpoint"
5. **Copy the Signing Secret** (starts with `whsec_...`) - you'll need this for `.env`

### Test Webhook

1. In the webhook details page, click "Send test webhook"
2. Select an event (e.g., `invoice.paid`)
3. Click "Send test webhook"
4. Verify HERMES receives and processes it

---

## Step 5: Get API Keys

### For Development (Test Mode)

1. Go to **Developers** → **API keys**
2. Ensure "Test mode" toggle is ON (top right)
3. Copy keys:
   - **Publishable key**: Starts with `pk_test_...` (for frontend)
   - **Secret key**: Starts with `sk_test_...` (for backend)
4. Store in `.env`:
   ```bash
   STRIPE_API_KEY=sk_test_your-secret-key-here
   ```

### For Production (Live Mode)

⚠️ **Only after account is activated**

1. Toggle "Test mode" to OFF
2. Go to **Developers** → **API keys**
3. Copy keys:
   - **Publishable key**: Starts with `pk_live_...`
   - **Secret key**: Starts with `sk_live_...`
4. Store in GCP Secret Manager (for production):
   ```bash
   echo "sk_live_your-secret-key" | gcloud secrets create STRIPE_API_KEY --data-file=-
   ```

---

## Step 6: Configure HERMES Environment

Add these variables to your `.env` file:

```bash
# Stripe API Keys
STRIPE_API_KEY=sk_test_your-secret-key-here  # or sk_live_ for production
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-signing-secret-here

# Stripe Product/Price IDs
STRIPE_PRICE_ENTERPRISE=price_your-enterprise-plan-id-here
# Optional: Add overage price if using metered billing
# STRIPE_PRICE_OVERAGE=price_your-overage-price-id-here

# Billing Configuration
STRIPE_TRIAL_DAYS=0  # No trial period for enterprise
ENTERPRISE_PLAN_PRICE=2497  # Monthly price in dollars
MAX_MONTHLY_INTERACTIONS=10000  # Included in plan
OVERAGE_PRICE_PER_INTERACTION=0.25  # Per additional interaction
```

---

## Step 7: Test in Test Mode

### Create Test Customer

```python
import stripe
stripe.api_key = "sk_test_..."

# Create customer
customer = stripe.Customer.create(
    email="test@lawfirm.com",
    name="Test Law Firm",
    metadata={"hermes_user_id": "user_123"}
)
print(f"Customer ID: {customer.id}")
```

### Create Test Subscription

```python
# Create subscription
subscription = stripe.Subscription.create(
    customer=customer.id,
    items=[{"price": "price_your-enterprise-plan-id"}],
    metadata={"hermes_user_id": "user_123"}
)
print(f"Subscription ID: {subscription.id}")
print(f"Status: {subscription.status}")
```

### Test Payment

Use Stripe test cards:
- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **3D Secure**: `4000 0025 0000 3155`

Any future expiry date and any 3-digit CVC.

---

## Step 8: Configure Usage Metering (Optional)

If using metered billing for overages:

### Record Usage

```python
# Record interactions (called from hermes/billing/stripe_billing.py)
stripe.SubscriptionItem.create_usage_record(
    subscription_item_id,
    quantity=150,  # Number of interactions
    timestamp=int(time.time()),
    action='increment'
)
```

### View Usage

```bash
# Via Stripe CLI
stripe subscription_items usage_records list si_xxxxx

# Via Dashboard
# Go to Subscription → Usage tab
```

---

## Step 9: Set Up Customer Portal (Optional)

Allow customers to manage their own subscriptions:

1. Go to **Settings** → **Billing** → **Customer portal**
2. Enable features:
   - ✅ Update payment method
   - ✅ View invoices
   - ✅ Cancel subscription (optional)
   - ❌ Update subscription plan (disable for enterprise)
3. Configure branding:
   - Upload logo
   - Set colors
   - Customize text
4. Click "Save"

### Link to Customer Portal

```python
# Generate portal session
session = stripe.billing_portal.Session.create(
    customer=customer_id,
    return_url="https://hermes.yourlawfirm.com/billing"
)
# Redirect user to: session.url
```

---

## Troubleshooting

### Issue: Webhook Signature Verification Failed

**Error**: `stripe.error.SignatureVerificationError`

**Solutions**:
- Verify `STRIPE_WEBHOOK_SECRET` is correct
- Don't modify webhook request body before verification
- Check webhook endpoint uses `raw_body` (not parsed JSON)
- Ensure correct endpoint URL in Stripe dashboard

**Code Check**:
```python
# In hermes/billing/stripe_billing.py, verify:
sig_header = request.headers.get('Stripe-Signature')
event = stripe.Webhook.construct_event(
    payload=request.body,  # Must be raw bytes!
    sig_header=sig_header,
    secret=STRIPE_WEBHOOK_SECRET
)
```

### Issue: Payment Requires Action (3D Secure)

**Error**: `payment_intent.status == 'requires_action'`

**Solutions**:
- Frontend must handle 3D Secure authentication
- Use Stripe.js to confirm payment
- For backend-only: Use `payment_method_options[card][request_three_d_secure]='any'`

### Issue: Subscription Not Created

**Error**: Various subscription creation errors

**Common Causes**:
- Missing payment method attached to customer
- Price ID doesn't exist
- Insufficient permissions on API key
- Customer already has active subscription

**Debugging**:
```python
try:
    subscription = stripe.Subscription.create(...)
except stripe.error.StripeError as e:
    print(f"Error: {e.user_message}")
    print(f"Type: {type(e).__name__}")
    print(f"Code: {e.code}")
```

### Issue: Webhook Not Received

**Symptoms**: Events in Stripe Dashboard but not reaching HERMES

**Solutions**:
1. Check endpoint URL is accessible publicly
2. Verify endpoint returns 200 status code
3. Check HERMES logs for webhook errors
4. Test with `stripe trigger` CLI command
5. Verify webhook is not disabled in dashboard

**Local Testing with ngrok**:
```bash
# Install ngrok
npm install -g ngrok

# Start HERMES locally
uvicorn hermes.main:app --host 0.0.0.0 --port 8000

# Expose via ngrok
ngrok http 8000

# Use ngrok URL in Stripe webhook:
# https://abc123.ngrok.io/api/billing/webhook
```

---

## Test vs. Live Mode

### Test Mode
- Use test API keys (`sk_test_...`)
- Use test credit cards
- No real charges
- Separate data from live mode
- Can reset test data anytime

### Live Mode
- Use live API keys (`sk_live_...`)
- Real credit cards only
- Real charges processed
- Cannot reset data
- Requires activated account

**Switching**: Toggle "Test mode" in dashboard (top right)

---

## Security Best Practices

### API Key Security
- ✅ Store secret keys in environment variables or GCP Secret Manager
- ✅ Never commit API keys to git
- ✅ Use different keys for test and live
- ✅ Rotate keys periodically
- ❌ Never expose secret keys in frontend code
- ❌ Never log API keys

### Webhook Security
- ✅ Always verify webhook signatures
- ✅ Use HTTPS endpoints only
- ✅ Validate event types before processing
- ✅ Make webhook handler idempotent (handle duplicates)
- ❌ Don't trust webhook payload without verification

### PCI Compliance
- ✅ Use Stripe.js or Elements for card collection
- ✅ Never handle raw card numbers in backend
- ✅ Use Stripe's hosted checkout or payment pages
- ✅ Store only Stripe customer/payment method IDs
- ❌ Never store card numbers, CVV, or PIN

---

## Monitoring & Alerts

### Dashboard Monitoring

1. Go to **Home** in Stripe Dashboard
2. Monitor:
   - **Payments**: Success rate, volume
   - **Disputes**: Chargebacks
   - **Customers**: Growth, churn
   - **MRR**: Monthly recurring revenue

### Email Alerts

1. Go to **Settings** → **Notifications**
2. Enable alerts for:
   - Failed payments
   - Disputes/chargebacks
   - Successful payments (optional)
   - Refunds

### Radar for Fraud Detection

Stripe Radar (included) automatically blocks fraudulent payments:
- 3D Secure enforcement
- CVC checks
- Address verification
- Velocity checks
- Machine learning fraud detection

---

## Cost Considerations

### Stripe Fees

**Standard Pricing**:
- **Card payments**: 2.9% + $0.30 per successful charge
- **ACH Direct Debit**: 0.8% capped at $5
- **International cards**: +1.5%
- **Currency conversion**: +1%

**Example for HERMES**:
- Enterprise plan: $2,497/month
- Stripe fee: $72.41 + $0.30 = $72.71
- Net revenue: $2,424.29

### Additional Costs

- **Disputes**: $15 per dispute (refunded if won)
- **Radar for Fraud Teams**: $0.05 per screened transaction (optional)
- **Billing**: Free for subscriptions
- **Invoices**: Free

### Cost Optimization

- Use ACH when possible (0.8% vs 2.9%)
- Implement retry logic for failed payments
- Prevent disputes with clear billing descriptors
- Use Stripe's dunning emails for failed payments

---

## Compliance

### PCI DSS
- Stripe is PCI Level 1 certified
- Using Stripe.js/Elements makes you PCI SAQ A compliant (simplest)
- Never handle raw card data in your backend

### Tax Collection
- **Stripe Tax** (optional): Automatic tax calculation and remittance
- **Cost**: 0.5% of transaction amount
- **Setup**: Enable in Settings → Tax

### Data Retention
- Customer data: Retained until deleted
- Logs: 90 days (rolling)
- Invoices: Retained indefinitely
- Cards: Deleted when detached from customer

---

## Going Live Checklist

Before switching to live mode:

- [ ] Stripe account fully activated
- [ ] Bank account added for payouts
- [ ] Business details verified
- [ ] Products and prices created in live mode
- [ ] Webhook endpoint configured with live URL
- [ ] Live API keys stored in GCP Secret Manager
- [ ] Test subscription flow end-to-end in test mode
- [ ] Webhook signature verification working
- [ ] Customer portal configured (optional)
- [ ] Email notifications enabled
- [ ] Billing descriptor set correctly
- [ ] Terms of service linked in checkout

---

## Next Steps

Once Stripe is configured:

1. ✅ Test subscription creation with test card
2. ✅ Verify webhook events are received
3. ✅ Test failed payment scenarios
4. ✅ Configure customer portal (optional)
5. ✅ Switch to live mode when ready
6. ✅ Continue with deployment: [DEPLOYMENT.md](../../DEPLOYMENT.md)

---

## Support

- **Stripe Docs**: [stripe.com/docs](https://stripe.com/docs)
- **Stripe Support**: [support.stripe.com](https://support.stripe.com/)
- **API Reference**: [stripe.com/docs/api](https://stripe.com/docs/api)
- **HERMES Support**: info@parallax-ai.app

---

**Last Updated**: 2024-11-19
