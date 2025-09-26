# HERMES Enterprise SaaS Deployment Guide

**GCP App Engine Deployment for Law Firm Clients ($2,497/month)**

This guide covers the complete deployment process for the HERMES Enterprise SaaS platform on Google Cloud Platform App Engine. This deployment model prevents self-hosting and ensures controlled access for law firm clients.

## 🚨 Important: SaaS-Only Deployment

⚠️ **CRITICAL SECURITY NOTICE**
- Self-hosting is **prohibited** under enterprise license terms
- Only authorized GCP deployments are permitted
- All deployments require valid enterprise API keys
- Unauthorized deployments violate licensing agreements

## 🏗️ Prerequisites

### Required Accounts & Services

1. **Google Cloud Platform**
   - Active GCP project with billing enabled
   - App Engine admin permissions
   - Secret Manager API access
   - Compute Engine API access (for VPC connector)

2. **Supabase Database**
   - Enterprise Supabase account
   - PostgreSQL instance with row-level security
   - Service role key for backend access

3. **External APIs**
   - OpenAI API account (GPT-4 access required)
   - Stripe account for billing (live keys required)
   - Optional: Clio integration keys for CRM

### Local Environment

```bash
# Required tools
gcloud CLI (latest version)
Python 3.11+
Git
OpenSSL (for JWT key generation)
```

## 🚀 Deployment Process

### Step 1: Repository Setup

```bash
# Clone the enterprise repository (authorized access required)
git clone https://github.com/parallax-analytics/hermes-agent.git
cd hermes-agent

# Verify Docker files are removed (anti-self-hosting check)
ls -la | grep -E "(docker|Docker)" && echo "VIOLATION: Docker files found" || echo "✅ Docker files removed"
```

### Step 2: GCP Project Configuration

```bash
# Set your GCP project ID
export PROJECT_ID="your-hermes-enterprise-project"

# Authenticate with GCP
gcloud auth login
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable appengine.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```

### Step 3: Secret Configuration

```bash
# Run the secret configuration script
./deployment/setup-secrets.sh

# This will prompt for:
# - Supabase database URL
# - Supabase project URL and service key
# - OpenAI API key
# - Stripe API keys
# - JWT keys (auto-generated)
# - API key encryption secret (auto-generated)
```

### Step 4: VPC Connector (Optional - Enterprise Security)

For enhanced security, create a VPC connector for private Supabase access:

```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create hermes-connector \
    --network default \
    --region us-central1 \
    --range 10.8.0.0/28 \
    --min-instances 2 \
    --max-instances 10
```

### Step 5: Deploy to App Engine

```bash
# Run the deployment script
./deployment/deploy.sh

# The script will:
# 1. Validate enterprise prerequisites
# 2. Configure app.yaml with your project details
# 3. Deploy to App Engine with enterprise settings
# 4. Set up monitoring and alerting
# 5. Generate deployment report
```

### Step 6: DNS & SSL Configuration (Optional)

```bash
# Map custom domain (if using)
gcloud app domain-mappings create your-domain.com \
    --certificate-management=AUTOMATIC

# Note: DNS configuration required at your registrar
# Point your domain to ghs.googlehosted.com
```

## 🔐 Security Verification

### Post-Deployment Security Checks

```bash
# Test deployment security
curl -I https://$PROJECT_ID.appspot.com/health

# Verify API key authentication
curl -H "X-API-Key: herm_ent_test" \
     https://$PROJECT_ID.appspot.com/api/pricing

# Check security headers
curl -I https://$PROJECT_ID.appspot.com/
```

### Expected Security Headers

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-eval'
```

## 📊 Enterprise Client Configuration

### API Key Generation for Law Firms

```python
# Generate enterprise API key for law firm client
from hermes.auth.api_key_auth import create_enterprise_client_key

# Create key for law firm
key_info = await create_enterprise_client_key(
    law_firm_name="Smith & Associates",
    contact_email="it@smithlaw.com"
)

# Provides:
# - Secure API key (herm_ent_...)
# - Monthly pricing: $2,497
# - Usage limits: 10,000 interactions/month
# - Overage rate: $0.25 per interaction
```

### Client Integration Example

```bash
# Law firm API integration
curl -X POST https://$PROJECT_ID.appspot.com/api/voice/process \
  -H "Authorization: Bearer herm_ent_ABC123..." \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": "base64_encoded_audio",
    "session_id": "client_session_001",
    "law_firm_id": "firm_ABC123"
  }'
```

## 🏛️ Legal & Compliance

### Required Agreements

1. **Business Associate Agreement (BAA)**
   - HIPAA compliance for healthcare-related legal work
   - Template available at: legal@hermes-ai.com

2. **Enterprise Service Agreement**
   - SaaS terms and conditions
   - Pricing and usage terms
   - Support level agreements

3. **Data Processing Agreement (DPA)**
   - GDPR compliance for international clients
   - Data residency and retention policies

### Audit & Compliance Features

- **Immutable Audit Logs**: All interactions logged to Supabase
- **Data Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Access Controls**: Role-based permissions and API key authentication
- **Compliance Reporting**: SOC2, HIPAA, and legal industry reports

## 📈 Monitoring & Maintenance

### Built-in Monitoring

- **Health Checks**: `/health` endpoint for uptime monitoring
- **Metrics**: Prometheus metrics at `/metrics`
- **Security Status**: `/security/status` for compliance verification
- **Usage Tracking**: Automatic billing and usage enforcement

### GCP Monitoring Setup

```bash
# Create uptime check
gcloud alpha monitoring uptime create-config uptime-check.json

# Set up alerting policies
gcloud alpha monitoring policies create alerting-policy.json
```

### Performance Optimization

- **Auto-scaling**: App Engine handles traffic spikes automatically
- **CDN**: GCP CDN for static assets
- **Database**: Supabase with connection pooling
- **Caching**: Redis integration for session management

## 🆘 Troubleshooting

### Common Issues

1. **Secret Access Errors**
   ```bash
   # Verify secret permissions
   gcloud secrets list
   gcloud secrets describe SUPABASE_DATABASE_URL
   ```

2. **Database Connection Issues**
   ```bash
   # Test Supabase connectivity
   curl https://your-project.supabase.co/rest/v1/ \
        -H "apikey: your-anon-key"
   ```

3. **API Key Authentication Failures**
   ```bash
   # Verify API key format
   echo "API Key should start with: herm_ent_"
   ```

### Support Channels

- **Enterprise Support**: enterprise@hermes-ai.com
- **Technical Issues**: support@hermes-ai.com
- **Security Incidents**: security@hermes-ai.com
- **24/7 Emergency**: Call support number provided with API keys

## 💰 Billing & Cost Management

### Cost Estimation

**Monthly Costs (per law firm client):**
- HERMES Enterprise License: $2,497.00
- GCP App Engine: ~$150-300 (auto-scaling)
- Supabase Enterprise: ~$99-199
- External APIs (OpenAI, etc.): Variable based on usage

### Cost Optimization

- Use GCP committed use discounts for consistent traffic
- Optimize Supabase queries to reduce database costs
- Monitor OpenAI API usage to prevent unexpected charges
- Implement usage alerts for enterprise clients

## 🔄 Updates & Maintenance

### Rolling Updates

```bash
# Deploy new version with zero downtime
gcloud app deploy --no-promote --version v2
gcloud app services set-traffic default --splits v2=100
```

### Database Migrations

```bash
# Run Alembic migrations
python -c "from alembic import command; from alembic.config import Config; cfg = Config('alembic.ini'); command.upgrade(cfg, 'head')"
```

## 📞 Enterprise Support

**24/7 Support Included with Enterprise License**

- **Tier 1**: General platform and API issues
- **Tier 2**: Advanced technical and integration support
- **Tier 3**: Custom development and architecture consulting
- **Legal Tech Specialists**: Bar-certified support staff for legal industry questions

**Response Times:**
- Critical (system down): 1 hour
- High (degraded performance): 4 hours
- Medium (general issues): 24 hours
- Low (feature requests): 5 business days

---

**© 2024 Parallax Analytics LLC. Enterprise SaaS deployment only.**
**HERMES® - Authorized deployment required. Self-hosting prohibited.**