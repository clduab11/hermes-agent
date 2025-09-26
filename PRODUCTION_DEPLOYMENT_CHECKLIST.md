# HERMES Production Deployment Checklist

## 🚀 Complete Pre-Deployment Checklist for Cloud Demo Hosting

This checklist ensures HERMES is fully production-ready for secure cloud deployment on Google Cloud Platform, linkable from parallax-ai.app.

### 📋 Pre-Deployment Validation

- [ ] **Run Production Validation Script**
  ```bash
  ./scripts/validate-production.sh
  ```
  - All checks should pass (success rate 100%)
  - Address any failures before proceeding

### 🔧 Environment Setup

#### 1. Google Cloud Platform Setup
- [ ] **GCP Project Created**
  - Project ID: `hermes-legal-ai` (or your chosen ID)
  - Billing enabled
  - APIs enabled: App Engine, Secret Manager, Cloud Resource Manager

- [ ] **GCP Authentication**
  ```bash
  gcloud auth login
  gcloud config set project YOUR_PROJECT_ID
  ```

- [ ] **Enable Required APIs**
  ```bash
  gcloud services enable appengine.googleapis.com
  gcloud services enable secretmanager.googleapis.com
  gcloud services enable cloudresourcemanager.googleapis.com
  ```

#### 2. External Services Setup

##### Supabase (Database)
- [ ] **Supabase Project Created**
  - Enterprise plan recommended
  - PostgreSQL instance configured
  - Row-level security enabled
  - Service role key generated

- [ ] **Database Credentials**
  - `SUPABASE_URL`: `https://your-project.supabase.co`
  - `SUPABASE_SERVICE_ROLE_KEY`: Service role key
  - `DATABASE_URL`: PostgreSQL connection string

##### OpenAI (AI/LLM Services)
- [ ] **OpenAI API Account**
  - GPT-4 access confirmed
  - API key generated
  - Usage limits configured

##### Stripe (Billing)
- [ ] **Stripe Account Setup**
  - Live API keys generated
  - Webhook endpoints configured
  - Product pricing configured ($2,497/month)

##### Optional Integrations
- [ ] **Clio Integration** (if needed)
  - Developer account created
  - OAuth credentials configured
- [ ] **Additional APIs** (Zapier, GitHub, etc.)

### 🔐 Security Configuration

#### 1. Secrets Management
- [ ] **Generate JWT Keys**
  ```bash
  # Generate RSA key pair
  openssl genrsa -out jwt_private.pem 2048
  openssl rsa -in jwt_private.pem -pubout -out jwt_public.pem
  ```

- [ ] **Run Secret Setup Script**
  ```bash
  ./deployment/setup-secrets.sh
  ```

- [ ] **Verify All Secrets in GCP Secret Manager**
  - JWT_PRIVATE_KEY
  - JWT_PUBLIC_KEY
  - API_KEY_ENCRYPTION_SECRET
  - SUPABASE_DATABASE_URL
  - SUPABASE_PROJECT_URL
  - SUPABASE_SERVICE_KEY
  - OPENAI_API_KEY
  - STRIPE_API_KEY
  - STRIPE_WEBHOOK_SECRET

#### 2. Security Validation
- [ ] **Security Headers Configured**
  - HTTPS enforcement
  - CORS properly configured
  - CSP headers in place

- [ ] **Compliance Settings**
  - Audit logging enabled
  - Legal disclaimers active
  - HIPAA/SOC2 configuration verified

### 🏗️ Application Configuration

#### 1. Core Settings
- [ ] **Production Mode Enabled**
  - `DEBUG=false` in app.yaml
  - `DEMO_MODE=false` in app.yaml
  - Production environment variables set

- [ ] **Resource Allocation**
  - Memory: 8GB (configured in app.yaml)
  - CPU: 4 cores
  - Auto-scaling: 3-100 instances

#### 2. Database Setup
- [ ] **Database Migrations**
  ```bash
  # Run database migrations
  alembic upgrade head
  ```

- [ ] **Database Security**
  - RLS policies enabled
  - Multi-tenant isolation configured
  - Audit triggers in place

### 🌐 Network & Domain Configuration

#### 1. VPC Setup (Optional - Enhanced Security)
- [ ] **VPC Connector Created**
  ```bash
  gcloud compute networks vpc-access connectors create hermes-connector \
      --network default \
      --region us-central1 \
      --range 10.8.0.0/28
  ```

#### 2. Custom Domain (Optional)
- [ ] **Domain Verification**
  - Domain ownership verified in GCP
  - SSL certificate configured
  - DNS records updated

### 🚀 Deployment Process

#### 1. Pre-Deployment Checks
- [ ] **Code Repository Clean**
  - No debug code or test files
  - No Docker files (SaaS deployment only)
  - All secrets removed from code

- [ ] **Final Validation**
  ```bash
  ./scripts/validate-production.sh
  ```

#### 2. Deploy to Production
- [ ] **Run Deployment Script**
  ```bash
  export GCP_PROJECT_ID="your-project-id"
  export GCP_REGION="us-central1"
  ./scripts/deploy-gcp.sh
  ```

- [ ] **Verify Deployment**
  - Application accessible at App Engine URL
  - Health checks passing (`/health`, `/ready`, `/live`)
  - No error logs in GCP Console

#### 3. Post-Deployment Verification
- [ ] **Application Health**
  ```bash
  curl https://your-app-url.appspot.com/health
  curl https://your-app-url.appspot.com/ready
  ```

- [ ] **Security Endpoints**
  ```bash
  curl https://your-app-url.appspot.com/security/status
  ```

- [ ] **API Functionality**
  - Authentication working
  - Voice processing functional
  - WebSocket connections stable

### 📊 Monitoring & Alerting

#### 1. Google Cloud Monitoring
- [ ] **Uptime Checks Configured**
  - Health endpoint monitoring
  - SLA targets set (99.9% uptime)
  - Alert policies created

- [ ] **Performance Monitoring**
  - Response time tracking
  - Error rate monitoring
  - Resource utilization alerts

#### 2. Application Metrics
- [ ] **Prometheus Metrics**
  - Metrics endpoint accessible (`/metrics`)
  - Key performance indicators tracked
  - SLA dashboard configured (`/sla`)

### 🔒 Final Security Review

#### 1. Security Scan
- [ ] **Dependency Security Check**
  ```bash
  safety check --file requirements.txt
  ```

- [ ] **Code Security Analysis**
  ```bash
  bandit -r hermes/ -f json -o security-report.json
  ```

#### 2. Compliance Verification
- [ ] **SOC2 Readiness**
  - Audit logging enabled
  - Data encryption verified
  - Access controls in place

- [ ] **HIPAA Compliance**
  - Data handling procedures verified
  - Encryption at rest and in transit
  - Audit trails complete

### 🌟 Production Readiness Criteria

Your deployment is production-ready when ALL of the following are true:

✅ **Technical Readiness**
- All validation checks pass (100% success rate)
- No security vulnerabilities detected
- Performance benchmarks met
- Health checks responding correctly

✅ **Security Compliance**
- All secrets properly managed in GCP Secret Manager
- HTTPS enforced across all endpoints
- Security headers properly configured
- Multi-tenant isolation verified

✅ **Operational Readiness**
- Monitoring and alerting configured
- Deployment scripts tested and working
- Database migrations applied successfully
- Backup and recovery procedures documented

✅ **Business Readiness**
- Billing integration functional
- Legal compliance verified
- SLA monitoring active
- Support procedures in place

### 📞 Support & Resources

#### Documentation
- **Main Guide**: `DEPLOYMENT_GUIDE.md`
- **Security Guide**: `hermes/security/README.md`
- **API Documentation**: Available at `https://your-app-url/docs`

#### Support Contacts
- **Technical Support**: support@parallax-ai.app
- **Enterprise Sales**: enterprise@parallax-ai.app
- **Security Issues**: security@parallax-ai.app

#### Emergency Procedures
- **Incident Response**: Contact support immediately
- **Security Vulnerabilities**: Report via security@parallax-ai.app
- **Service Outages**: Check status page and contact support

---

## 🎯 Deployment Command Summary

Once all checklist items are complete, deploy with:

```bash
# 1. Final validation
./scripts/validate-production.sh

# 2. Set environment variables
export GCP_PROJECT_ID="your-hermes-project"
export GCP_REGION="us-central1"

# 3. Deploy to production
./scripts/deploy-gcp.sh

# 4. Verify deployment
curl https://your-app-url.appspot.com/health
```

**🎉 Congratulations! HERMES is now production-ready for secure cloud demo hosting!**