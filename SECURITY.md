# HERMES Security Documentation

This document outlines security measures, best practices, and compliance features implemented in HERMES.

---

## 🛡️ Security Overview

HERMES implements enterprise-grade security controls designed for law firms handling sensitive client information:

- **Authentication**: JWT-based with RS256 algorithm
- **Encryption**: TLS 1.3 in transit, AES-256 at rest
- **Secrets Management**: GCP Secret Manager (production)
- **Database Security**: Row-Level Security (RLS) policies
- **Audit Logging**: Immutable logs for compliance
- **Rate Limiting**: Protection against abuse
- **Input Validation**: All user inputs sanitized

**Reference**: `hermes/security/` modules, `security.yaml`

---

## 🔐 Authentication & Authorization

### JWT Authentication

**Algorithm**: RS256 (RSA 2048-bit)
**Token Types**:
- **Access Token**: 15-minute expiry (configurable)
- **Refresh Token**: 7-day expiry (configurable)

**Token Format**:
```json
{
  "sub": "user_id",
  "email": "user@lawfirm.com",
  "role": "admin",
  "iat": 1234567890,
  "exp": 1234568790
}
```

**Implementation**:
```python
# Location: hermes/auth/jwt_handler.py
from jose import jwt

def create_access_token(user_id: str, email: str):
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }
    return jwt.encode(payload, private_key, algorithm="RS256")
```

**Key Management**:
- Keys generated via `scripts/generate-secrets.sh`
- Stored in GCP Secret Manager (production)
- Rotated every 90 days (recommended)

### Role-Based Access Control (RBAC)

| Role | Permissions | Use Case |
|------|-------------|----------|
| **Admin** | Full access | Law firm administrators |
| **User** | Read/write own data | Attorneys, paralegals |
| **API** | Programmatic access | Integrations, automation |
| **Viewer** | Read-only | Billing, reporting |

**Enforcement**:
```python
@require_role("admin")
async def delete_user(user_id: str):
    # Only admins can delete users
    pass
```

---

## 🔒 Data Encryption

### Encryption in Transit (TLS 1.3)

**Enforced via security.yaml**:
```yaml
security:
  secure_ssl_redirect: true
  http_headers:
    Strict-Transport-Security: "max-age=31536000; includeSubDomains; preload"
```

**All endpoints require HTTPS**:
- API: `https://your-domain.com/api/*`
- WebSocket: `wss://your-domain.com/ws/*`
- Redirect HTTP → HTTPS (301 permanent)

**Certificate Management**:
- Auto-provisioned by GCP App Engine
- Automatic renewal
- TLS 1.3 enforced (TLS 1.2 minimum)

### Encryption at Rest (AES-256)

**Database**:
- Supabase: AES-256 encryption at rest
- Backups: Encrypted with same key
- Snapshots: Encrypted

**Sensitive Fields**:
```python
# Location: hermes/security/encryption.py
from cryptography.fernet import Fernet

def encrypt_api_key(plain_key: str) -> str:
    """Encrypt API key before storing in database"""
    fernet = Fernet(os.getenv("API_KEY_ENCRYPTION_SECRET"))
    return fernet.encrypt(plain_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt API key for use"""
    fernet = Fernet(os.getenv("API_KEY_ENCRYPTION_SECRET"))
    return fernet.decrypt(encrypted_key.encode()).decode()
```

**Encrypted Fields**:
- API keys
- OAuth tokens (Clio)
- Payment method tokens
- Personally identifiable information (PII)

---

## 🔑 Secrets Management

### Production (GCP Secret Manager)

**Configuration**:
```yaml
# app.yaml
env_variables:
  SECRETS_PROVIDER: "gcp"
  GCP_PROJECT_ID: "your-project-id"
```

**Access Pattern**:
```python
# Location: hermes/security/secrets_manager.py
from google.cloud import secretmanager

def get_secret(name: str) -> str:
    """Retrieve secret from GCP Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    path = f"projects/{PROJECT_ID}/secrets/{name}/versions/latest"
    response = client.access_secret_version(request={"name": path})
    return response.payload.data.decode("UTF-8")
```

**Cached**: Secrets cached for 5 minutes to reduce API calls

### Development (Environment Variables)

**Configuration**:
```yaml
# app.yaml (dev)
env_variables:
  SECRETS_PROVIDER: "env"
  OPENAI_API_KEY: "sk-..."  # Direct value
```

⚠️ **Not for production**: Secrets visible in logs

---

## 🗄️ Database Security

### Row-Level Security (RLS)

**Policy Example** (users table):
```sql
-- Users can only see their own profile
CREATE POLICY "users_select_own"
  ON users FOR SELECT
  USING (auth.uid() = id);

-- Users can only update their own profile
CREATE POLICY "users_update_own"
  ON users FOR UPDATE
  USING (auth.uid() = id);
```

**Multi-Tenant Isolation**:
```sql
-- Users can only see their own API keys
CREATE POLICY "api_keys_tenant_isolation"
  ON api_keys FOR ALL
  USING (user_id = auth.uid());
```

**Service Role Key**: Bypasses RLS for admin operations (use carefully)

### Connection Security

**SSL/TLS Enforced**:
```python
# Location: hermes/database/connection.py
DATABASE_URL = "postgresql://...?sslmode=require"
```

**Connection Pooling**:
```python
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True  # Verify connections
)
```

---

## 📝 Audit Logging

### What We Log

**Access Logs**:
- API requests (endpoint, user, timestamp)
- Database queries (for sensitive tables)
- Secret access (GCP Secret Manager)
- Authentication attempts (success/failure)

**Security Events**:
- Failed login attempts (potential brute force)
- Permission violations (unauthorized access)
- Data exports (PII/sensitive data)
- Configuration changes (security settings)

**Compliance Logs**:
- All client conversations (attorney-client privilege)
- Billing events (invoices, payments)
- Data deletion requests (GDPR)

### Log Format

**Structured JSON**:
```json
{
  "timestamp": "2024-11-19T12:34:56.789Z",
  "level": "INFO",
  "event": "api_request",
  "user_id": "user_123",
  "endpoint": "/api/matters",
  "method": "GET",
  "status": 200,
  "duration_ms": 45,
  "ip_address": "203.0.113.1",
  "user_agent": "HERMES-Client/1.0"
}
```

### Log Retention

| Log Type | Retention | Location |
|----------|-----------|----------|
| **Access Logs** | 90 days | GCP Cloud Logging |
| **Security Logs** | 7 years | GCP Cloud Logging (legal) |
| **Audit Logs** | 7 years | Supabase + GCP Logging |

**Immutable**: Logs cannot be modified or deleted (tamper-evident)

---

## 🚦 Rate Limiting

**Configuration** (security.yaml):
```yaml
rate_limits:
  # Standard API calls
  - path: "/api/*"
    rate: "1000/hour"
  
  # Voice processing (expensive)
  - path: "/ws/voice"
    rate: "100/hour"
  
  # Authentication endpoints
  - path: "/auth/*"
    rate: "50/hour"
```

**Implementation**:
```python
# Location: hermes/security/rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/matters")
@limiter.limit("1000/hour")
async def create_matter():
    # Rate limited to 1000 requests/hour per IP
    pass
```

**Exceed Limit**: HTTP 429 (Too Many Requests)

---

## 🛡️ Security Headers

**Enforced via security.yaml**:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS protection |
| `Strict-Transport-Security` | `max-age=31536000` | Force HTTPS |
| `Content-Security-Policy` | Restrictive | Prevent XSS/injection |
| `Referrer-Policy` | `strict-origin` | Privacy protection |

**CSP Example**:
```
Content-Security-Policy: default-src 'self'; 
  script-src 'self' 'unsafe-eval'; 
  style-src 'self' 'unsafe-inline'; 
  img-src 'self' data: https:; 
  connect-src 'self' https://api.openai.com wss:
```

---

## 🔍 Input Validation & Sanitization

### API Input Validation

**Using Pydantic**:
```python
from pydantic import BaseModel, EmailStr, Field

class CreateUserRequest(BaseModel):
    email: EmailStr  # Validates email format
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., regex=r"^\+?1?\d{10,15}$")
```

**Validation Errors**: HTTP 422 (Unprocessable Entity)

### SQL Injection Prevention

**Parameterized Queries**:
```python
# Bad (vulnerable)
query = f"SELECT * FROM users WHERE email = '{email}'"

# Good (safe)
query = "SELECT * FROM users WHERE email = :email"
result = await db.execute(query, {"email": email})
```

**ORM Protection**: SQLAlchemy escapes all inputs automatically

### XSS Prevention

**Output Escaping**:
```python
from markupsafe import escape

def render_response(user_input: str):
    return escape(user_input)  # Escapes HTML chars
```

**CSP Headers**: Prevent inline scripts (see Security Headers)

---

## 🔐 Compliance Features

### HIPAA Compliance (Health Insurance Portability and Accountability Act)

**Applicable**: If handling healthcare-related legal matters

**Controls**:
- ✅ Encryption in transit and at rest
- ✅ Access controls (RBAC)
- ✅ Audit logging (immutable)
- ✅ Business Associate Agreement (BAA) with Supabase
- ✅ Data retention policies
- ✅ Incident response plan

**Business Associate Agreement**:
- Supabase: Available on Pro tier
- OpenAI: Available for enterprise (contact sales)
- Stripe: PCI-compliant, HIPAA BAA available

### GDPR Compliance (General Data Protection Regulation)

**Applicable**: If serving EU clients

**Controls**:
- ✅ Data minimization (collect only necessary data)
- ✅ Right to access (users can export data)
- ✅ Right to deletion (users can delete account)
- ✅ Right to rectification (users can update data)
- ✅ Data portability (export in JSON format)
- ✅ Breach notification (<72 hours)

**Data Processing Agreement (DPA)**:
- Supabase: GDPR-compliant DPA included
- OpenAI: DPA available
- Stripe: GDPR-compliant

### SOC 2 Type II Compliance

**Controls Implemented**:
- ✅ **Security**: Encryption, access controls, firewalls
- ✅ **Availability**: Uptime monitoring, redundancy
- ✅ **Processing Integrity**: Input validation, error handling
- ✅ **Confidentiality**: Encryption, data classification
- ✅ **Privacy**: Consent, data minimization, deletion

**Vendor Compliance**:
- GCP: SOC 2 Type II certified
- Supabase: SOC 2 Type II certified
- OpenAI: SOC 2 Type II certified
- Stripe: PCI-DSS Level 1 (highest)

### Attorney-Client Privilege Protection

**Special Handling**:
```python
# Mark conversations as privileged
conversation.is_privileged = True
conversation.retention_years = 7  # Legal retention requirement

# Prevent accidental disclosure
if conversation.is_privileged:
    # Extra encryption
    # No training data
    # Restricted access
    pass
```

**Compliance**:
- ✅ No AI training on privileged conversations
- ✅ Encrypted storage with access controls
- ✅ Audit trail of all access
- ✅ 7-year retention (minimum)
- ✅ Secure deletion after retention period

---

## 🚨 Incident Response

### Security Incident Process

1. **Detection**: Monitoring alerts, user reports
2. **Containment**: Isolate affected systems
3. **Investigation**: Root cause analysis
4. **Remediation**: Fix vulnerability
5. **Notification**: Notify affected parties (<72hrs GDPR)
6. **Post-Mortem**: Document lessons learned

### Incident Types

| Type | Severity | Response Time | Notification Required |
|------|----------|---------------|----------------------|
| **Data Breach** | P0 | <1 hour | Yes (GDPR/HIPAA) |
| **Unauthorized Access** | P1 | <4 hours | Yes (affected users) |
| **DDoS Attack** | P1 | <4 hours | No (unless prolonged) |
| **Vulnerability Disclosed** | P2 | <24 hours | If exploited |

### Contacts

- **Security Issues**: security@parallax-ai.app
- **Privacy Issues**: privacy@parallax-ai.app
- **General Support**: info@parallax-ai.app

---

## 📋 Security Checklist

### Pre-Deployment

- [ ] All secrets stored in GCP Secret Manager (not .env)
- [ ] JWT keys generated and rotated
- [ ] Database RLS policies enabled
- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] Security headers configured (security.yaml)
- [ ] Rate limiting enabled
- [ ] Audit logging enabled
- [ ] Firewalls configured (allow only 443, 8080)
- [ ] Service accounts have minimal permissions
- [ ] Vulnerability scan completed (bandit, safety)

### Post-Deployment

- [ ] Health checks passing (/health, /ready, /live)
- [ ] Logs flowing to GCP Cloud Logging
- [ ] Monitoring alerts configured
- [ ] Budget alerts set up
- [ ] Backup verification (Supabase)
- [ ] Incident response plan documented
- [ ] Team trained on security procedures

### Ongoing

- [ ] Weekly security log review
- [ ] Monthly vulnerability scan
- [ ] Quarterly secret rotation
- [ ] Annual penetration test
- [ ] Annual compliance audit

---

## 🔧 Security Configuration

### Enable All Security Features

1. **Generate Secrets**:
   ```bash
   ./scripts/generate-secrets.sh
   ```

2. **Upload to Secret Manager**:
   ```bash
   ./scripts/upload-secrets.sh
   ```

3. **Configure app.yaml**:
   ```yaml
   env_variables:
     SECRETS_PROVIDER: "gcp"
     DEBUG: "false"
     AUDIT_LOGGING: "true"
     ENABLE_DISCLAIMERS: "true"
   ```

4. **Deploy**:
   ```bash
   ./scripts/deploy-gcp.sh
   ```

5. **Verify**:
   ```bash
   ./scripts/validate-production.sh --pre-deploy
   ```

---

## 📞 Support

Security questions or concerns?
- **Security Team**: security@parallax-ai.app
- **Bug Bounty**: Coming soon
- **Responsible Disclosure**: security@parallax-ai.app

---

**Last Updated**: 2024-11-19

**Note**: This document is a living document. Security practices evolve. Review and update quarterly.
