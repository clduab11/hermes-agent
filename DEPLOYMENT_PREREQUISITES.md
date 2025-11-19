# HERMES Deployment Prerequisites

This document lists all required accounts, tools, permissions, and setup steps before deploying HERMES to production.

---

## ✅ Required Accounts & Services

### 1. Google Cloud Platform (GCP) ⚠️ **CRITICAL**

**Status**: Required for production deployment

**What You Need**:
- GCP account with billing enabled
- Active project with billing account attached
- Project ID noted for configuration

**Setup Steps**:
1. Create GCP account at [cloud.google.com](https://cloud.google.com/)
2. Create new project: `HERMES Legal AI` (or your preferred name)
3. Enable billing for the project
4. Note your Project ID (e.g., `hermes-legal-ai-123456`)

**Cost Estimate**: See [COST_ESTIMATION.md](COST_ESTIMATION.md)
- **Expected**: $400-1200/month
- **Demo Setup**: $50-100/month (using app.yaml.demo)

**IAM Roles Required**:
- `App Engine Admin` (for deployment)
- `Secret Manager Admin` (for secrets)
- `Compute Admin` (for VPC connector)
- `Service Account User` (for service accounts)
- `Cloud Build Editor` (for builds)

---

### 2. Supabase Database ⚠️ **CRITICAL**

**Status**: Required for data persistence

**What You Need**:
- Supabase project (Free or Pro tier)
- Database connection string
- Service role key
- Project URL

**Setup Steps**:
See detailed guide: [docs/services/supabase-setup.md](docs/services/supabase-setup.md)

1. Create account at [supabase.com](https://supabase.com/)
2. Create new project (choose region close to GCP region)
3. Get credentials from Settings → Database & API
4. Apply database migrations (see setup guide)

**Cost Estimate**:
- **Free Tier**: $0/month (good for development)
- **Pro Tier**: $25/month + usage (recommended for production)
- **Enterprise**: $100-250/month (high-scale production)

**Database Requirements**:
- PostgreSQL 15+
- Row-Level Security (RLS) enabled
- Connection pooling configured
- SSL/TLS enforced

---

### 3. OpenAI API ⚠️ **CRITICAL**

**Status**: Required for AI features

**What You Need**:
- OpenAI account with API access
- API key with GPT-4 access
- Billing configured

**Setup Steps**:
See detailed guide: [docs/services/openai-setup.md](docs/services/openai-setup.md)

1. Create account at [platform.openai.com](https://platform.openai.com/)
2. Request GPT-4 API access (may require verification)
3. Add payment method
4. Generate API key
5. Set usage limits ($500/month recommended)

**Cost Estimate**:
- **Development**: $50-100/month (light testing)
- **Production**: $100-500/month (1-5M tokens)
- **High Usage**: $500-2000/month (5M+ tokens)

**Rate Limits**:
- Free tier: 3 requests/minute
- Tier 1 ($5+ spent): 60 requests/minute
- Tier 3 ($100+ spent): 3500 requests/minute

---

### 4. Stripe Billing 🔵 **HIGH PRIORITY**

**Status**: Required for billing features (can be disabled for internal use)

**What You Need**:
- Stripe account (live mode)
- Product created: $2,497/month subscription
- Overage product: $0.25 per interaction
- Webhook endpoint configured
- Publishable & secret API keys

**Setup Steps**:
See detailed guide: [docs/services/stripe-setup.md](docs/services/stripe-setup.md)

1. Create account at [stripe.com](https://stripe.com/)
2. Activate account (provide business info)
3. Create products and pricing
4. Configure webhook endpoint
5. Get API keys (test and live)

**Cost Estimate**:
- **Stripe Fees**: 2.9% + $0.30 per transaction
- **Monthly Base**: ~$0-50 depending on volume

**Compliance**:
- PCI-DSS compliant (Stripe handles)
- Tax calculation (Stripe Tax optional)
- Receipt generation automatic

---

### 5. Redis Cache 🟢 **OPTIONAL (Recommended)**

**Status**: Optional but highly recommended for performance

**What You Need**:
- Redis instance (managed or self-hosted)
- Connection URL
- SSL/TLS configured

**Setup Steps**:
See detailed guide: [docs/services/redis-setup.md](docs/services/redis-setup.md)

**Hosting Options**:
1. **GCP Memorystore** (recommended for GCP deployment)
   - Cost: $50-200/month
   - Fully managed, auto-scaling
   
2. **Redis Cloud** (multi-cloud)
   - Free tier: 30MB (dev only)
   - Paid: $10-100/month
   
3. **Upstash** (serverless Redis)
   - Pay-per-request pricing
   - Good for low-traffic sites

**Cost Estimate**: $0-200/month (optional feature)

**Performance Impact**:
- **With Redis**: 10-50ms response times
- **Without Redis**: 50-200ms response times (in-memory fallback)

---

## 🛠️ Required Tools

### Development Tools

| Tool | Version | Purpose | Install Link |
|------|---------|---------|--------------|
| **Python** | 3.11+ | Runtime | [python.org](https://www.python.org/downloads/) |
| **pip** | Latest | Package manager | Included with Python |
| **Git** | Latest | Version control | [git-scm.com](https://git-scm.com/) |
| **OpenSSL** | 1.1+ | Key generation | Included on Linux/Mac |

### Deployment Tools

| Tool | Version | Purpose | Install Link |
|------|---------|---------|--------------|
| **gcloud CLI** | Latest | GCP deployment | [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install) |
| **Python venv** | 3.11+ | Virtual environments | Included with Python |

### Optional Tools

| Tool | Purpose | Install Link |
|------|---------|--------------|
| **Docker** | Local testing | [docker.com](https://www.docker.com/) |
| **Postman** | API testing | [postman.com](https://www.postman.com/) |
| **VS Code** | Code editor | [code.visualstudio.com](https://code.visualstudio.com/) |

---

## 📋 IAM Permissions Checklist

### GCP Service Account Permissions

For App Engine default service account (`[PROJECT-ID]@appspot.gserviceaccount.com`):

- [ ] `roles/secretmanager.secretAccessor` - Access secrets
- [ ] `roles/cloudsql.client` - Connect to databases
- [ ] `roles/logging.logWriter` - Write logs
- [ ] `roles/monitoring.metricWriter` - Write metrics
- [ ] `roles/storage.objectViewer` - Read static files

### Your User Account Permissions

For deploying HERMES:

- [ ] `roles/appengine.appAdmin` - Deploy to App Engine
- [ ] `roles/secretmanager.admin` - Manage secrets
- [ ] `roles/compute.networkAdmin` - Create VPC connectors
- [ ] `roles/iam.serviceAccountUser` - Use service accounts
- [ ] `roles/cloudbuild.builds.editor` - Trigger builds

**How to Grant**:
```bash
# Grant to service account
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:PROJECT_ID@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Grant to your user
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:your-email@example.com" \
  --role="roles/appengine.appAdmin"
```

---

## 💰 Cost Summary

### Minimum Production Budget

| Service | Monthly Cost | Required |
|---------|-------------|----------|
| GCP App Engine | $150-480 | ✅ Yes |
| Supabase Pro | $100-250 | ✅ Yes |
| OpenAI API | $100-500 | ✅ Yes |
| Stripe Fees | 2.9% + $0.30 | ✅ Yes |
| GCP Secret Manager | $5-10 | ✅ Yes |
| Redis (Optional) | $0-200 | ⚠️ Recommended |
| **Total** | **$455-1440/month** | - |

### Demo/Development Budget

| Service | Monthly Cost | Required |
|---------|-------------|----------|
| GCP App Engine (demo) | $50-100 | ✅ Yes |
| Supabase Free | $0 | ✅ Yes |
| OpenAI API (light) | $50-100 | ✅ Yes |
| Stripe (test mode) | $0 | ✅ Yes |
| GCP Secret Manager | $5 | ✅ Yes |
| **Total** | **$105-205/month** | - |

See [COST_ESTIMATION.md](COST_ESTIMATION.md) for detailed breakdown.

---

## 🌐 Network & Domain Setup

### Domain Configuration (Optional)

If using custom domain (e.g., `hermes.yourlawfirm.com`):

1. **Register Domain**: Use any domain registrar
2. **DNS Configuration**: Point to Google App Engine
3. **SSL Certificate**: Auto-provisioned by GCP
4. **Verify Ownership**: Via GCP Console

**GCP Custom Domain Setup**:
```bash
gcloud app domain-mappings create hermes.yourlawfirm.com
# Follow instructions to update DNS records
```

### VPC & Networking

**VPC Connector** (for private Supabase access):
- Name: `hermes-connector`
- Region: Same as App Engine region
- IP Range: `10.8.0.0/28`

Setup script: `./scripts/setup-vpc-connector.sh`

---

## ✅ API Limits & Quotas

### OpenAI API Quotas

| Tier | Monthly Spend | Requests/Min | Tokens/Min |
|------|---------------|--------------|------------|
| Free | $0 | 3 | 40,000 |
| Tier 1 | $5+ | 60 | 60,000 |
| Tier 2 | $50+ | 3,500 | 80,000 |
| Tier 3 | $100+ | 3,500 | 160,000 |

**Production Recommendation**: Tier 3 ($100+ spend history)

### GCP Quotas

Check current quotas:
```bash
gcloud compute project-info describe --project=PROJECT_ID
```

**Critical Quotas**:
- App Engine instances: Default 20 (increase if needed)
- Secret Manager secrets: Default 1000
- VPC Connectors: Default 10 per region

**How to Request Increase**:
1. Go to GCP Console → IAM & Admin → Quotas
2. Filter by service (e.g., "App Engine")
3. Select quota and click "Edit Quotas"
4. Submit increase request (usually approved in 2-3 days)

### Supabase Limits

| Plan | Databases | Storage | Bandwidth | Connections |
|------|-----------|---------|-----------|-------------|
| Free | 2 | 500MB | 2GB | 60 |
| Pro | Unlimited | 8GB | 50GB | 120 |
| Enterprise | Unlimited | Custom | Custom | Custom |

**Production Recommendation**: Pro tier minimum

---

## 🔍 Verification Steps

### Pre-Deployment Checklist

Before running `./scripts/deploy-gcp.sh`:

#### Accounts Verified
- [ ] GCP project created and billing enabled
- [ ] Supabase project created and accessible
- [ ] OpenAI API key generated and working
- [ ] Stripe account activated (if using billing)

#### Tools Installed
- [ ] `gcloud` CLI installed and authenticated
- [ ] Python 3.11+ installed
- [ ] Git installed
- [ ] OpenSSL available

#### Credentials Obtained
- [ ] Database connection string (from Supabase)
- [ ] Supabase service role key
- [ ] OpenAI API key
- [ ] Stripe API keys (test and live)
- [ ] JWT keys generated (or use script)

#### Permissions Granted
- [ ] GCP IAM roles assigned
- [ ] Service account has Secret Manager access
- [ ] Your user can deploy to App Engine

#### Configuration Complete
- [ ] `.env.template` copied to `.env`
- [ ] All required environment variables set
- [ ] Secrets generated (run `./scripts/generate-secrets.sh`)

#### Services Configured
- [ ] Database migrations applied (`alembic upgrade head`)
- [ ] Stripe products and prices created
- [ ] Webhooks configured (if using Stripe)

### Test Connectivity

```bash
# Test Supabase connection
psql "YOUR_DATABASE_URL"

# Test OpenAI API
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"

# Test Stripe API
curl https://api.stripe.com/v1/balance \
  -u YOUR_STRIPE_SECRET_KEY:

# Test GCP authentication
gcloud auth list
```

### Run Validation Script

```bash
# Comprehensive pre-deployment validation
./scripts/validate-production.sh --pre-deploy
```

This will check:
- All environment variables set
- External service connectivity
- GCP authentication
- Required APIs enabled
- Secret Manager access
- Database migrations status

---

## 🆘 Common Issues

### Issue: GCP Billing Not Enabled

**Error**: `Billing account for project '[PROJECT_ID]' is not found`

**Solution**:
1. Go to [GCP Console → Billing](https://console.cloud.google.com/billing)
2. Create or link billing account
3. Enable billing for your project

### Issue: App Engine Not Initialized

**Error**: `App Engine application does not exist`

**Solution**:
```bash
gcloud app create --project=PROJECT_ID --region=us-central1
```

### Issue: API Not Enabled

**Error**: `API [appengine.googleapis.com] not enabled on project`

**Solution**:
```bash
gcloud services enable appengine.googleapis.com --project=PROJECT_ID
```

### Issue: OpenAI Rate Limited

**Error**: `Rate limit reached for requests`

**Solution**:
- Check current tier at [platform.openai.com/account/limits](https://platform.openai.com/account/limits)
- Add payment method to increase tier
- Wait and retry (rate limits reset every minute)

### Issue: Supabase Connection Failed

**Error**: `FATAL: password authentication failed`

**Solution**:
- Verify `DATABASE_URL` is correct
- Check Supabase project is not paused
- Ensure your IP is not blocked (Supabase Auth settings)
- Try direct connection with `psql` to verify credentials

---

## 📞 Support

Need help with prerequisites?

- **Documentation**: Check individual service setup guides in `docs/services/`
- **GCP Issues**: [GCP Support](https://cloud.google.com/support)
- **Supabase Issues**: [Supabase Support](https://supabase.com/support)
- **OpenAI Issues**: [OpenAI Help](https://help.openai.com/)
- **General HERMES**: info@parallax-ai.app

---

## ✅ Ready to Deploy?

Once all prerequisites are met:

1. ✅ Read [DEPLOYMENT.md](DEPLOYMENT.md)
2. ✅ Review [COST_ESTIMATION.md](COST_ESTIMATION.md)
3. ✅ Check [SECURITY.md](SECURITY.md)
4. ✅ Run `./scripts/validate-production.sh --pre-deploy`
5. ✅ Deploy: `./scripts/deploy-gcp.sh`

---

**Last Updated**: 2024-11-19
