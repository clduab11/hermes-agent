# 🚀 HabitFlow Deployment Checklist

## Pre-Deployment Setup

### 1. Supabase Setup ✅

**Action Items:**
- [ ] Create Supabase project at https://supabase.com
- [ ] Run database schema: `/db/habit_tracker_schema.sql`
- [ ] Run subscription schema: `/db/subscriptions_schema.sql`
- [ ] Enable Google OAuth (optional)
- [ ] Copy Project URL and anon key

**SQL Commands to run in Supabase SQL Editor:**
```sql
-- First run habit_tracker_schema.sql
-- Then run subscriptions_schema.sql
```

**Keys needed:**
- `SUPABASE_URL`: https://[your-project].supabase.co
- `SUPABASE_ANON_KEY`: eyJ... (public anon key)
- `SUPABASE_SERVICE_ROLE_KEY`: eyJ... (secret service role key - DO NOT expose to frontend!)

---

### 2. Stripe Setup ✅

**Action Items:**
- [ ] Create Stripe account at https://stripe.com
- [ ] Create products in Stripe Dashboard:

**Pro Plan:**
```
Product: HabitFlow Pro
Monthly Price: $9.99/month (recurring)
Annual Price: $99/year (recurring)
```

**Premium Plan:**
```
Product: HabitFlow Premium
Monthly Price: $19.99/month (recurring)
Annual Price: $199/year (recurring)
```

- [ ] Copy all 4 Price IDs
- [ ] Update Price IDs in `frontend/src/habit-tracker/types/subscription.ts`
- [ ] Set up webhook endpoint: `https://[your-domain]/api/stripe/webhook`
- [ ] Select webhook events:
  - `checkout.session.completed`
  - `customer.subscription.created`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.paid`
  - `invoice.payment_failed`

**Keys needed:**
- `STRIPE_PUBLISHABLE_KEY`: pk_live_... (or pk_test_... for testing)
- `STRIPE_SECRET_KEY`: sk_live_... (or sk_test_... for testing)
- `STRIPE_WEBHOOK_SECRET`: whsec_...

---

### 3. Environment Variables ✅

**Create `.env.production` file:**

```env
# Supabase (Frontend - safe to expose)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key

# Stripe (Frontend - safe to expose)
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_your_key_here

# App Config (Frontend)
VITE_APP_NAME=HabitFlow
VITE_APP_URL=https://habitflow.com
VITE_API_URL=https://habitflow.com

# Backend Only (Add in Vercel Dashboard - NEVER commit these!)
STRIPE_SECRET_KEY=sk_live_your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

---

## Vercel Deployment ✅

### 1. Install Vercel CLI (Optional)

```bash
npm install -g vercel
```

### 2. Deploy via GitHub (Recommended)

**Steps:**
1. Push code to GitHub (already done! ✅)
2. Go to https://vercel.com
3. Click "Import Project"
4. Select your GitHub repo: `clduab11/hermes-agent`
5. Configure:
   - **Framework Preset:** Vite
   - **Root Directory:** `./`
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Output Directory:** `frontend/dist`
   - **Install Command:** `cd api && npm install && cd ../frontend && npm install`

6. Add Environment Variables (in Vercel Dashboard):
   ```
   VITE_SUPABASE_URL
   VITE_SUPABASE_ANON_KEY
   VITE_STRIPE_PUBLISHABLE_KEY
   VITE_APP_NAME
   VITE_APP_URL
   VITE_API_URL
   STRIPE_SECRET_KEY (secret)
   STRIPE_WEBHOOK_SECRET (secret)
   SUPABASE_SERVICE_ROLE_KEY (secret)
   ```

7. Click "Deploy"

### 3. API Routes Setup

Vercel will automatically detect API routes in `/api` directory and create serverless functions.

**Endpoints created:**
- `https://your-domain/api/stripe/create-checkout-session`
- `https://your-domain/api/stripe/create-portal-session`
- `https://your-domain/api/stripe/webhook`

---

## Post-Deployment Testing ✅

### 1. Test Free Tier
- [ ] Visit your deployed URL
- [ ] Sign up with email
- [ ] Create 3 habits
- [ ] Complete a habit
- [ ] Check analytics

### 2. Test Upgrade Flow (Use Stripe Test Mode)
- [ ] Go to /pricing
- [ ] Click "Start Free Trial"
- [ ] Use test card: `4242 4242 4242 4242`
- [ ] Verify subscription created
- [ ] Create 4th habit (should work now)
- [ ] Check billing page

### 3. Test Stripe Webhooks
- [ ] Complete a test payment
- [ ] Check Vercel logs for webhook events
- [ ] Verify database updated correctly
- [ ] Check payment history in billing page

### 4. Test Billing Portal
- [ ] Go to /billing
- [ ] Click "Manage Billing"
- [ ] Update payment method
- [ ] Cancel subscription
- [ ] Reactivate subscription

---

## Production Readiness Checklist ✅

### Security
- [ ] All secrets in environment variables (not in code)
- [ ] HTTPS enabled (automatic with Vercel)
- [ ] RLS policies enabled in Supabase
- [ ] Stripe webhook signature verification
- [ ] CORS configured properly

### Performance
- [ ] Build size < 1MB (currently ~800KB ✅)
- [ ] Assets cached (configured in vercel.json ✅)
- [ ] Database indexes created ✅
- [ ] Images optimized

### Monitoring
- [ ] Vercel Analytics enabled
- [ ] Stripe Dashboard monitoring
- [ ] Supabase logs accessible
- [ ] Error tracking (Sentry recommended)

### Legal & Compliance
- [ ] Privacy Policy page
- [ ] Terms of Service page
- [ ] Cookie consent (if needed)
- [ ] GDPR compliance
- [ ] Data deletion capability

---

## Go Live Checklist ✅

### Pre-Launch
- [ ] Switch Stripe from test to live mode
- [ ] Update Stripe keys in Vercel
- [ ] Verify all environment variables
- [ ] Test full user journey
- [ ] Set up custom domain
- [ ] Configure DNS
- [ ] SSL certificate active

### Launch Day
- [ ] Monitor error logs
- [ ] Watch Stripe dashboard
- [ ] Test signup flow
- [ ] Test payment flow
- [ ] Respond to first users quickly

### Post-Launch (First Week)
- [ ] Monitor daily active users
- [ ] Track conversion rate
- [ ] Check for errors
- [ ] Gather user feedback
- [ ] Fix critical bugs immediately

---

## Monitoring Dashboard URLs

- **Vercel Dashboard:** https://vercel.com/dashboard
- **Supabase Dashboard:** https://app.supabase.com
- **Stripe Dashboard:** https://dashboard.stripe.com
- **GitHub Actions:** https://github.com/clduab11/hermes-agent/actions

---

## Troubleshooting

### "Stripe key not configured"
- Check Vercel environment variables
- Ensure `VITE_STRIPE_PUBLISHABLE_KEY` is set
- Redeploy after adding

### "API endpoint 404"
- Check `/api` directory deployed
- Verify Vercel detected serverless functions
- Check function logs in Vercel

### "Supabase connection failed"
- Verify URL and keys correct
- Check Supabase project not paused
- Test from Supabase dashboard

### "Webhook not working"
- Verify webhook URL in Stripe
- Check webhook secret matches
- Test with Stripe CLI: `stripe listen --forward-to localhost:3000/api/stripe/webhook`

---

## Support

- **Documentation:** See `PRODUCTION_DEPLOYMENT_GUIDE.md`
- **Issues:** Create GitHub issue
- **Email:** support@habitflow.com

---

## Estimated Timeline

- **Setup (Supabase + Stripe):** 30-45 minutes
- **Deployment (Vercel):** 10-15 minutes
- **Testing:** 30 minutes
- **Go Live:** 5 minutes

**Total: ~1.5 hours to production** 🚀

---

## Current Status

Branch: `claude/habit-tracking-platform-01K8KYUy5Mcp4gKxmDzbxxj2`

**Completed:**
✅ Full habit tracking platform
✅ Subscription system
✅ Stripe integration
✅ Database schema
✅ Frontend UI
✅ API endpoints
✅ CI/CD pipeline
✅ Documentation

**Next Steps:**
1. Set up Supabase project
2. Set up Stripe account
3. Deploy to Vercel
4. Test everything
5. Go live! 🎉

---

**Ready to deploy? Follow the steps above!** 🚀
