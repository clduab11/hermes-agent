# 🚀 HabitFlow - Production Deployment Guide

## Quick Start

This guide will help you deploy HabitFlow to production with Stripe monetization enabled.

---

## 📋 Prerequisites

Before deploying, ensure you have:

- ✅ GitHub account (for code hosting & CI/CD)
- ✅ Vercel account (for frontend hosting)
- ✅ Supabase account (for database & auth)
- ✅ Stripe account (for payments)
- ✅ Domain name (optional, but recommended)

---

## 1️⃣ Database Setup (Supabase)

### Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Click "New Project"
3. Choose organization and set project details
4. Wait for database to be provisioned (~2 minutes)

### Run Database Migrations

1. Go to SQL Editor in Supabase Dashboard
2. Run the following schemas in order:

**First:** Run `/db/habit_tracker_schema.sql`
```sql
-- This creates all habit tracking tables, functions, and RLS policies
```

**Second:** Run `/db/subscriptions_schema.sql`
```sql
-- This creates subscription, billing, and referral tables
```

### Configure Authentication

1. Go to Authentication > Providers
2. Enable Email provider
3. (Optional) Enable Google OAuth:
   - Go to Google Cloud Console
   - Create OAuth 2.0 credentials
   - Add authorized redirect URL: `https://[your-project-ref].supabase.co/auth/v1/callback`
   - Copy Client ID and Secret to Supabase

### Get API Keys

1. Go to Settings > API
2. Copy:
   - Project URL: `https://[your-project-ref].supabase.co`
   - `anon` public key

---

## 2️⃣ Stripe Setup

### Create Stripe Account

1. Go to [stripe.com](https://stripe.com)
2. Create account or sign in
3. Complete business verification (required for live mode)

### Create Products & Prices

1. Go to Products in Stripe Dashboard
2. Create products for each tier:

**Pro Plan:**
- Product Name: "HabitFlow Pro"
- Description: "Unlimited habits, AI recommendations, and premium features"
- Pricing:
  - Monthly: $9.99/month (Recurring)
  - Annual: $99/year (Recurring)
- Copy the Price IDs (e.g., `price_1ABC...`)

**Premium Plan:**
- Product Name: "HabitFlow Premium"
- Description: "Everything in Pro plus unlimited AI and API access"
- Pricing:
  - Monthly: $19.99/month (Recurring)
  - Annual: $199/year (Recurring)
- Copy the Price IDs

### Configure Webhooks

1. Go to Developers > Webhooks
2. Add endpoint: `https://your-domain.com/api/stripe/webhook`
3. Select events to listen to:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.paid`
   - `invoice.payment_failed`
4. Copy webhook signing secret

### Get API Keys

1. Go to Developers > API keys
2. Copy:
   - Publishable key (starts with `pk_`)
   - Secret key (starts with `sk_`)

---

## 3️⃣ Environment Configuration

Create a `.env.production` file in `/frontend/`:

```env
# Supabase
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key

# Stripe
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_your_key_here

# App Configuration
VITE_APP_NAME=HabitFlow
VITE_APP_URL=https://habitflow.com
VITE_API_URL=https://api.habitflow.com

# Optional: OpenRouter for AI
VITE_OPENROUTER_API_KEY=your_openrouter_key
```

### Update Stripe Price IDs

Edit `/frontend/src/habit-tracker/types/subscription.ts`:

```typescript
stripePriceIds: {
  monthly: 'price_YOUR_ACTUAL_PRICE_ID',  // Replace with real IDs
  annual: 'price_YOUR_ACTUAL_PRICE_ID',
},
```

---

## 4️⃣ Deploy to Vercel

### Connect GitHub

1. Push code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Click "Import Project"
4. Select your GitHub repository
5. Configure project:
   - Framework Preset: Vite
   - Build Command: `cd frontend && npm run build`
   - Output Directory: `frontend/dist`
   - Install Command: `cd frontend && npm install`

### Add Environment Variables

In Vercel Dashboard:
1. Go to Settings > Environment Variables
2. Add all variables from `.env.production`:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
   - `VITE_STRIPE_PUBLISHABLE_KEY`
   - etc.

3. Make sure to select "Production" environment

### Deploy

1. Click "Deploy"
2. Wait for build to complete (~2-3 minutes)
3. Get deployment URL: `https://your-project.vercel.app`

### Custom Domain (Optional)

1. Go to Settings > Domains
2. Add your domain (e.g., `habitflow.com`)
3. Follow DNS configuration instructions
4. Wait for SSL certificate to be issued (~10 minutes)

---

## 5️⃣ CI/CD Setup (GitHub Actions)

### Configure Secrets

1. Go to your GitHub repository
2. Settings > Secrets and variables > Actions
3. Add repository secrets:

```
VERCEL_TOKEN=your_vercel_token
VERCEL_ORG_ID=your_org_id
VERCEL_PROJECT_ID=your_project_id
```

To get these values:
- Vercel Token: Vercel > Settings > Tokens > Create Token
- Org ID & Project ID: Run `vercel project ls` in terminal

### Enable Workflows

The CI/CD pipeline is already configured in `.github/workflows/ci.yml`:
- ✅ Runs tests on every push
- ✅ Builds project
- ✅ Deploys to Vercel on main branch
- ✅ Runs security scans

---

## 6️⃣ Backend API Setup (Required for Stripe)

You need a backend to handle Stripe webhooks and checkout sessions. Options:

### Option A: Vercel Serverless Functions

Create `/api/stripe/create-checkout-session.ts`:

```typescript
import Stripe from 'stripe';
import { createClient } from '@supabase/supabase-js';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);
const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!
);

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { priceId, userId } = req.body;

  try {
    // Get or create Stripe customer
    const { data: subscription } = await supabase
      .from('subscriptions')
      .select('stripe_customer_id')
      .eq('user_id', userId)
      .single();

    let customerId = subscription?.stripe_customer_id;

    if (!customerId) {
      const customer = await stripe.customers.create({
        metadata: { userId },
      });
      customerId = customer.id;
    }

    // Create checkout session
    const session = await stripe.checkout.sessions.create({
      customer: customerId,
      payment_method_types: ['card'],
      line_items: [{ price: priceId, quantity: 1 }],
      mode: 'subscription',
      success_url: req.body.successUrl,
      cancel_url: req.body.cancelUrl,
      subscription_data: {
        trial_period_days: 14,
      },
    });

    res.status(200).json({ sessionId: session.id });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}
```

### Option B: Use Existing Backend

If you have a backend API, integrate Stripe there and update the API URLs in the frontend.

---

## 7️⃣ Testing in Production

### Test Free Tier

1. Visit your deployed URL
2. Sign up with email
3. Verify you can:
   - Create up to 3 habits
   - Track completions
   - See basic analytics

### Test Paid Tier (Stripe Test Mode)

1. Use Stripe test mode keys
2. Go to /pricing page
3. Click "Start Free Trial"
4. Use test card: `4242 4242 4242 4242`
5. Verify subscription is created

### Monitor Errors

1. Check Vercel logs
2. Check Supabase logs
3. Check Stripe webhook logs

---

## 8️⃣ Go Live Checklist

### Pre-Launch

- [ ] All tests passing
- [ ] Database schema deployed
- [ ] Stripe products created
- [ ] Environment variables set
- [ ] Custom domain configured
- [ ] SSL certificate active
- [ ] Privacy policy page added
- [ ] Terms of service page added

### Launch Day

- [ ] Switch Stripe from test to live mode
- [ ] Update Stripe keys in Vercel
- [ ] Verify webhook endpoints work
- [ ] Test full signup → payment flow
- [ ] Monitor error logs
- [ ] Set up analytics (PostHog/Mixpanel)
- [ ] Set up error tracking (Sentry)

### Post-Launch

- [ ] Monitor conversion rates
- [ ] Track churn
- [ ] Set up customer support (email)
- [ ] Create help documentation
- [ ] Set up backup system

---

## 9️⃣ Monitoring & Analytics

### Recommended Tools

**Error Tracking:**
- Sentry (errors & performance)
- Vercel Analytics (built-in)

**Product Analytics:**
- PostHog (free, self-hosted option)
- Mixpanel (user journeys)
- Plausible (privacy-focused)

**Business Metrics:**
- Stripe Dashboard (MRR, churn)
- Google Analytics (traffic)
- Custom Supabase queries (engagement)

### Key Metrics to Track

- Daily/Monthly Active Users (DAU/MAU)
- Free → Paid conversion rate
- Churn rate
- Monthly Recurring Revenue (MRR)
- Customer Lifetime Value (LTV)
- Habit completion rate
- Average habits per user

---

## 🔧 Troubleshooting

### "Stripe publishable key not configured"

- Check environment variables in Vercel
- Ensure `VITE_STRIPE_PUBLISHABLE_KEY` is set
- Redeploy after adding

### "Supabase connection failed"

- Verify Supabase URL and key
- Check if RLS policies are enabled
- Ensure database is not paused (free tier)

### "Checkout not working"

- Check backend API is deployed
- Verify Stripe webhook secret
- Check browser console for errors
- Test in Stripe test mode first

### "Database migrations failed"

- Run schemas in correct order
- Check for syntax errors
- Verify you have admin access
- Try running line by line

---

## 💡 Cost Estimate

### Monthly Costs (1,000 users)

| Service | Plan | Cost |
|---------|------|------|
| Vercel | Pro | $20/month |
| Supabase | Pro | $25/month |
| Stripe | Standard | 2.9% + $0.30/transaction |
| Domain | - | $12/year |
| **Total** | | ~$50/month + fees |

### Scaling (10,000 users)

- Vercel: $150/month (Enterprise)
- Supabase: $100/month (Team)
- Stripe fees: ~$600/month (assuming 5% conversion)
- **Total: ~$850/month**

---

## 📚 Additional Resources

- [Supabase Docs](https://supabase.com/docs)
- [Stripe Docs](https://stripe.com/docs)
- [Vercel Docs](https://vercel.com/docs)
- [React Router](https://reactrouter.com/)
- [Tailwind CSS](https://tailwindcss.com/)

---

## 🆘 Support

For deployment help:
- GitHub Issues: [your-repo/issues](https://github.com/your-repo/issues)
- Email: support@habitflow.com
- Discord: [habitflow-community](https://discord.gg/habitflow)

---

**Ready to launch? Let's transform habit tracking! 🚀**
