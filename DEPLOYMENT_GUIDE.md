# HERMES Enterprise SaaS - GCP Deployment Guide

## Overview

This guide provides complete instructions for deploying HERMES Enterprise Legal AI Voice Reception System to Google Cloud Platform App Engine with enterprise-grade security, monitoring, and scalability.

## Architecture

```
Internet → Cloud Load Balancer → App Engine → Supabase Database
                                    ↓
                           Google Secret Manager
                                    ↓
                         Cloud Monitoring & Logging
```

## Prerequisites

### Required Software
- Google Cloud SDK (gcloud CLI)
- Python 3.11+
- Git
- OpenSSL (for JWT key generation)

### Required Services
- Google Cloud Project with billing enabled
- Supabase account for database
- Stripe account for billing
- OpenAI API key
- (Optional) Clio developer account

### Environment Setup
```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
source ~/.bashrc

# Authenticate with Google Cloud
gcloud auth login
gcloud config set project hermes-legal-ai

# Clone repository
git clone <repository-url>
cd hermes-agent
```

## Deployment Process

### Step 1: Prepare Secrets

#### 1.1 Generate JWT Keys
```bash
# Generate RSA key pair for JWT authentication
./scripts/manage-secrets.sh generate-keys
```

#### 1.2 Configure Required Secrets
```bash
# List required secrets
./scripts/manage-secrets.sh list

# Create each secret interactively
./scripts/manage-secrets.sh create SUPABASE_DATABASE_URL
./scripts/manage-secrets.sh create OPENAI_API_KEY
./scripts/manage-secrets.sh create STRIPE_API_KEY
# ... continue for all required secrets
```

#### 1.3 Required Secret Values

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `SUPABASE_DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SUPABASE_PROJECT_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | `eyJ...` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `JWT_PRIVATE_KEY` | RSA private key for JWT | `-----BEGIN RSA PRIVATE KEY-----...` |
| `JWT_PUBLIC_KEY` | RSA public key for JWT | `-----BEGIN PUBLIC KEY-----...` |
| `STRIPE_API_KEY` | Stripe secret key | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook endpoint secret | `whsec_...` |
| `API_KEY_ENCRYPTION_SECRET` | Fernet key for API key encryption | 32-byte base64 encoded key |
| `CLIO_CLIENT_SECRET` | Clio OAuth client secret | Optional |
| `CLIO_TOKEN_ENCRYPTION_KEY` | Fernet key for Clio tokens | Optional |

### Step 2: Deploy Application

#### 2.1 Automated Deployment
```bash
# Run the complete deployment script
./scripts/deploy-gcp.sh
```

#### 2.2 Manual Deployment Steps
```bash
# Enable required APIs
gcloud services enable appengine.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudmonitoring.googleapis.com

# Create App Engine application
gcloud app create --region=us-central1

# Deploy the application
gcloud app deploy --promote --stop-previous-version
```

### Step 3: Configure Monitoring

```bash
# Set up comprehensive monitoring
./scripts/setup-monitoring.sh
```

### Step 4: Configure Custom Domain (Optional)

```bash
# Map custom domain
gcloud app domain-mappings create hermes.parallax-ai.app

# Update DNS records (manual step)
# Add CNAME record: hermes.parallax-ai.app → ghs.googlehosted.com

# Verify domain mapping
gcloud app domain-mappings list
```

### Step 5: SSL Certificate Setup

```bash
# Create managed SSL certificate
gcloud compute ssl-certificates create hermes-ssl \
    --domains=hermes.parallax-ai.app \
    --global

# Verify certificate status
gcloud compute ssl-certificates describe hermes-ssl --global
```

## Configuration

### Environment Variables

The following environment variables are configured in `app.yaml`:

```yaml
env_variables:
  # Production mode
  DEBUG: "false"
  DEMO_MODE: "false"

  # API configuration
  API_HOST: "0.0.0.0"
  API_PORT: "8080"

  # Security settings
  CORS_ALLOW_ORIGINS: "https://hermes.parallax-ai.app,https://admin.hermes.parallax-ai.app"
  JWT_ALGORITHM: "RS256"
  ACCESS_TOKEN_EXPIRE_MINUTES: "15"

  # Legal compliance
  CONFIDENCE_THRESHOLD: "0.9"
  ENABLE_DISCLAIMERS: "true"
  AUDIT_LOGGING: "true"
```

### Auto-scaling Configuration

```yaml
automatic_scaling:
  min_instances: 3
  max_instances: 100
  target_cpu_utilization: 0.65
  target_throughput_utilization: 0.70
  cool_down_period_sec: 120
  max_concurrent_requests: 1000
  max_idle_instances: 5
```

### Resource Allocation

```yaml
resources:
  cpu: 4
  memory_gb: 8
```

## Security

### Authentication
- API Key authentication for all endpoints
- JWT tokens for dashboard access
- Rate limiting on all API endpoints
- CORS restrictions to allowed domains only

### Data Protection
- End-to-end encryption with TLS 1.3
- Secrets stored in Google Secret Manager
- Database connections over SSL
- Audit logging for all operations

### Compliance
- SOC 2 Type II compliance ready
- HIPAA compliant architecture
- GDPR compliant data handling
- Complete audit trails

## Monitoring & Alerting

### Key Metrics
- Request rate and response times
- Error rates and availability
- Voice processing latency
- Lead conversion rates
- System resource usage

### Alert Conditions
- Error rate > 5% for 5 minutes
- Response time > 5 seconds
- Service availability < 99.5%
- Memory usage > 85%

### Dashboards
- Production overview dashboard
- Business metrics dashboard
- Error reporting console

## Maintenance

### Regular Tasks

#### Daily
- Monitor error rates and response times
- Review high-value lead alerts
- Check system resource usage

#### Weekly
- Review and tune alert thresholds
- Analyze performance trends
- Update security patches

#### Monthly
- Rotate API keys and secrets
- Review and update monitoring dashboards
- Conduct security assessment

### Backup & Recovery

#### Database Backups
- Supabase provides automatic backups
- Additional backup configuration in Supabase dashboard
- Point-in-time recovery available

#### Application Backups
- Source code in Git repository
- Secrets in Google Secret Manager
- Configuration in Infrastructure as Code

### Scaling Considerations

#### Horizontal Scaling
- App Engine automatically scales based on traffic
- Configure min/max instances based on expected load
- Monitor and adjust scaling parameters

#### Vertical Scaling
- Increase CPU/memory allocation in app.yaml
- Monitor resource usage patterns
- Consider upgrading instance types for sustained high load

## Troubleshooting

### Common Issues

#### Deployment Failures
```bash
# Check deployment logs
gcloud app logs tail -s default

# Verify secrets exist
./scripts/manage-secrets.sh validate

# Check service status
gcloud app describe
```

#### Performance Issues
```bash
# View performance metrics
gcloud monitoring dashboards list

# Check error rates
gcloud logging read "resource.type=gae_app AND severity>=ERROR" --limit=50

# Monitor resource usage
gcloud app instances list
```

#### Database Connection Issues
```bash
# Test database connectivity
gcloud secrets versions access latest --secret="SUPABASE_DATABASE_URL"

# Check VPC connector status
gcloud compute networks vpc-access connectors list
```

### Emergency Procedures

#### Service Outage Response
1. Check monitoring dashboards
2. Review error logs
3. Scale up instances if needed
4. Rollback to previous version if necessary
5. Notify stakeholders

#### Security Incident Response
1. Immediately rotate affected credentials
2. Review audit logs
3. Block suspicious IP addresses
4. Notify security team
5. Document incident

## API Documentation

### Base URL
```
Production: https://hermes.parallax-ai.app/v1
```

### Authentication
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://hermes.parallax-ai.app/v1/status
```

### Key Endpoints
- `GET /health` - Health check
- `GET /status` - Detailed system status
- `POST /api/voice/process` - Process voice input
- `GET /api/analytics/realtime` - Real-time analytics
- `GET /dashboard` - Web dashboard

## Support

### Technical Support
- **Email**: ops@parallax-ai.com
- **Slack**: #hermes-operations
- **Emergency**: PagerDuty escalation

### Documentation
- **API Docs**: https://hermes.parallax-ai.app/api-docs
- **Status Page**: https://status.hermes.parallax-ai.app
- **Monitoring**: Google Cloud Console

## Compliance & Legal

### Data Retention
- Voice recordings: 90 days
- Client information: As per legal requirements
- Audit logs: 7 years

### Privacy
- All data encrypted at rest and in transit
- Minimal data collection principles
- Right to deletion supported

### Terms of Service
- Enterprise SaaS agreement required
- Usage limits enforced
- Compliance with legal industry standards

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-15 | Initial production release |

---

**© 2024 Parallax AI. All rights reserved.**

This deployment guide is confidential and proprietary. Distribution is restricted to authorized personnel only.