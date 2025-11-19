# GCP Secret Manager Setup Guide

This guide walks you through setting up Google Cloud Secret Manager for secure secrets storage in production HERMES deployments.

---

## Overview

GCP Secret Manager stores sensitive configuration values:
- Database credentials
- API keys (OpenAI, Stripe)
- JWT private/public keys
- Encryption secrets
- OAuth client secrets

**Why Secret Manager?**
- Encrypted at rest and in transit
- Versioning and rotation support
- Fine-grained IAM access control
- Audit logging of access
- Integration with GCP services

**Reference**: `hermes/security/secrets_manager.py`, `scripts/upload-secrets.sh`

---

## Prerequisites

- GCP project created
- `gcloud` CLI installed and authenticated
- Billing enabled on project

---

## Step 1: Enable Secret Manager API

```bash
# Set your project
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID

# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com
```

---

## Step 2: Grant IAM Permissions

### For Your User (to create secrets)

```bash
# Get your email
export USER_EMAIL=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")

# Grant Secret Manager Admin role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="user:$USER_EMAIL" \
    --role="roles/secretmanager.admin"
```

### For App Engine (to access secrets at runtime)

```bash
# Get App Engine service account
export SERVICE_ACCOUNT="$PROJECT_ID@appspot.gserviceaccount.com"

# Grant Secret Accessor role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"
```

---

## Step 3: Create Secrets

### Required Secrets for HERMES

Create these secrets before deployment:

1. **Database Secrets**
   - `SUPABASE_DATABASE_URL`
   - `SUPABASE_PROJECT_URL`
   - `SUPABASE_SERVICE_KEY`

2. **AI Service Secrets**
   - `OPENAI_API_KEY`

3. **Authentication Secrets**
   - `JWT_PRIVATE_KEY`
   - `JWT_PUBLIC_KEY`
   - `API_KEY_ENCRYPTION_SECRET`

4. **Billing Secrets**
   - `STRIPE_API_KEY`
   - `STRIPE_WEBHOOK_SECRET`

5. **Integration Secrets** (optional)
   - `CLIO_CLIENT_SECRET`
   - `CLIO_TOKEN_ENCRYPTION_KEY`

### Manual Secret Creation

```bash
# Create secret with value from stdin
echo -n "your-secret-value" | gcloud secrets create SECRET_NAME --data-file=-

# Example: OpenAI API Key
echo -n "sk-your-openai-api-key" | gcloud secrets create OPENAI_API_KEY --data-file=-

# Example: Database URL
echo -n "postgresql://user:pass@host:5432/db" | gcloud secrets create SUPABASE_DATABASE_URL --data-file=-
```

### Multi-line Secrets (JWT Keys)

For secrets with newlines (e.g., PEM keys):

```bash
# Create temporary file
cat > /tmp/jwt_private.pem << 'EOF'
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
...
-----END PRIVATE KEY-----
EOF

# Create secret from file
gcloud secrets create JWT_PRIVATE_KEY --data-file=/tmp/jwt_private.pem

# Clean up
rm /tmp/jwt_private.pem
```

---

## Step 4: Automated Secret Upload

Use the provided script for bulk secret creation:

### Generate Secrets

```bash
# Generate JWT keys and encryption secrets
./scripts/generate-secrets.sh

# Output: .env.secrets file
```

### Upload All Secrets

```bash
# Upload secrets from .env.secrets to GCP Secret Manager
./scripts/upload-secrets.sh

# This will:
# 1. Parse .env.secrets
# 2. Create/update secrets in GCP
# 3. Grant access to App Engine service account
# 4. Verify uploads
```

See: [Automation Scripts](#automation-scripts-phase-4) for script details

---

## Step 5: Grant Access to Secrets

For each secret, grant the App Engine service account access:

```bash
# Grant access to a single secret
gcloud secrets add-iam-policy-binding SECRET_NAME \
    --member="serviceAccount:$PROJECT_ID@appspot.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Or use loop for all secrets
for SECRET in OPENAI_API_KEY JWT_PRIVATE_KEY SUPABASE_DATABASE_URL; do
    gcloud secrets add-iam-policy-binding $SECRET \
        --member="serviceAccount:$PROJECT_ID@appspot.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
done
```

---

## Step 6: Configure HERMES to Load Secrets

### Update app.yaml

```yaml
env_variables:
  # Enable GCP Secret Manager
  SECRETS_PROVIDER: "gcp"
  GCP_PROJECT_ID: "your-project-id"
  
  # Other non-secret config...
  DEBUG: "false"
  API_HOST: "0.0.0.0"
```

### Runtime Secret Loading

HERMES automatically loads secrets at runtime using `hermes/security/secrets_manager.py`:

```python
from hermes.security.secrets_manager import get_secret

# Secrets are loaded transparently
database_url = get_secret("SUPABASE_DATABASE_URL")
openai_key = get_secret("OPENAI_API_KEY")
```

**No code changes required** - existing environment variable usage works automatically.

---

## Step 7: Verify Secret Access

### List Secrets

```bash
# List all secrets in project
gcloud secrets list

# View secret metadata (not the value)
gcloud secrets describe SECRET_NAME
```

### Access Secret Value

```bash
# Get latest version
gcloud secrets versions access latest --secret="SECRET_NAME"

# Get specific version
gcloud secrets versions access 1 --secret="SECRET_NAME"
```

### Test from App Engine Context

```python
# In a Cloud Function or App Engine, test secret access
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
name = f"projects/{PROJECT_ID}/secrets/{SECRET_NAME}/versions/latest"
response = client.access_secret_version(request={"name": name})
secret_value = response.payload.data.decode("UTF-8")
print(f"Secret loaded: {secret_value[:10]}...")  # First 10 chars only
```

---

## Step 8: Secret Rotation

### Update Secret Value

```bash
# Add new version
echo -n "new-secret-value" | gcloud secrets versions add SECRET_NAME --data-file=-

# The old version is preserved (for rollback)
```

### Disable Old Version

```bash
# Disable specific version (soft delete)
gcloud secrets versions disable 1 --secret="SECRET_NAME"

# Enable if needed
gcloud secrets versions enable 1 --secret="SECRET_NAME"
```

### Destroy Old Version

```bash
# Permanently delete version (cannot be undone)
gcloud secrets versions destroy 1 --secret="SECRET_NAME"
```

### Rotation Best Practices

1. **Add new version** (don't delete old immediately)
2. **Deploy app** with new version
3. **Monitor** for errors
4. **Disable old version** after 24-48 hours
5. **Destroy old version** after 7 days (if no issues)

---

## Naming Conventions

### Secret Names

Use consistent naming:
- Use UPPER_SNAKE_CASE
- Match environment variable names
- Prefix optional: `hermes_` or `prod_`

**Examples**:
- ✅ `OPENAI_API_KEY`
- ✅ `JWT_PRIVATE_KEY`
- ✅ `hermes_SUPABASE_DATABASE_URL`
- ❌ `openai-api-key` (wrong case)
- ❌ `jwt.private.key` (wrong separator)

---

## Cost Considerations

### Pricing

| Operation | Cost | Free Tier |
|-----------|------|-----------|
| **Secret Version** | $0.06 per version/month | 6 secrets free |
| **Access Operation** | $0.03 per 10,000 accesses | 10,000 free/month |
| **Rotation** | Free (just new version) | - |

### Example Costs for HERMES

**Secrets**:
- 10 secrets × 1 version each = 10 versions
- Cost: 10 - 6 (free) = 4 × $0.06 = $0.24/month

**Access Operations**:
- 100 requests/min × 60 min × 24 hr × 30 days = 4.3M/month
- Each request loads ~5 secrets = 21.5M accesses
- Cost: (21.5M - 10k free) / 10k × $0.03 = $64.50/month

**Total**: ~$65/month (included in cost estimate)

### Cost Optimization

```python
# Bad: Load secret on every request
def handle_request():
    api_key = get_secret("OPENAI_API_KEY")  # Expensive!
    ...

# Good: Cache secrets
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_secret(name):
    return get_secret(name)

def handle_request():
    api_key = get_cached_secret("OPENAI_API_KEY")  # Cached!
    ...
```

**HERMES automatically caches secrets** to reduce costs.

---

## Security Best Practices

### Access Control

- ✅ Use least-privilege principle
- ✅ Grant access per-secret (not blanket access)
- ✅ Use service-specific service accounts
- ✅ Audit access logs regularly
- ❌ Don't grant `secretmanager.admin` to service accounts

### Audit Logging

View who accessed secrets:

```bash
# View audit logs
gcloud logging read "resource.type=secret_manager_secret" \
    --limit=50 \
    --format=json

# Filter by secret
gcloud logging read "resource.labels.secret_id=OPENAI_API_KEY" \
    --limit=10
```

### Rotation Policy

- **High-risk secrets** (API keys): Rotate every 30-90 days
- **Medium-risk** (encryption keys): Rotate every 6-12 months
- **Low-risk** (non-sensitive config): Rotate as needed

---

## Troubleshooting

### Issue: Permission Denied

**Error**: `Permission 'secretmanager.versions.access' denied`

**Solutions**:
- Grant `roles/secretmanager.secretAccessor` to service account
- Verify IAM binding: `gcloud secrets get-iam-policy SECRET_NAME`
- Check service account email is correct
- Wait 1-2 minutes for IAM propagation

### Issue: Secret Not Found

**Error**: `Secret [projects/xxx/secrets/yyy] not found`

**Solutions**:
- Verify secret exists: `gcloud secrets list`
- Check spelling (case-sensitive!)
- Ensure correct project ID
- Create secret if missing

### Issue: Multi-line Secret Corrupted

**Error**: JWT key invalid or newlines lost

**Solutions**:
- Use `--data-file` (not command line echo)
- Preserve newlines in file
- Verify with: `gcloud secrets versions access latest --secret=JWT_PRIVATE_KEY`
- Use base64 encoding if needed

### Issue: High Costs

**Error**: Secret Manager bill is unexpectedly high

**Solutions**:
- Check access frequency (may be loading too often)
- Implement caching (HERMES has built-in caching)
- Reduce number of secret versions (clean up old)
- Use environment variables for non-sensitive config

---

## Alternative: Environment Variables

For development, you can skip Secret Manager:

### In app.yaml

```yaml
env_variables:
  SECRETS_PROVIDER: "env"  # Use environment variables
  OPENAI_API_KEY: "sk-your-key"  # Direct in app.yaml
  # ... other secrets
```

⚠️ **Not recommended for production** (secrets visible in logs, version control risk)

---

## Automation Scripts (Phase 4)

HERMES provides scripts to automate secret management:

### Generate Secrets

```bash
# Generate JWT keys and encryption secrets
./scripts/generate-secrets.sh

# Output: .env.secrets (DO NOT COMMIT!)
```

### Upload to GCP

```bash
# Bulk upload all secrets
./scripts/upload-secrets.sh

# With dry-run (preview changes)
./scripts/upload-secrets.sh --dry-run
```

See [Phase 4: Automation Scripts](#phase-4-automation-scripts) for details.

---

## Next Steps

Once Secret Manager is configured:

1. ✅ Enable Secret Manager API
2. ✅ Grant IAM permissions
3. ✅ Create all required secrets
4. ✅ Grant service account access
5. ✅ Configure app.yaml with `SECRETS_PROVIDER=gcp`
6. ✅ Test secret access
7. ✅ Continue with deployment: [DEPLOYMENT.md](../../DEPLOYMENT.md)

---

## Support

- **GCP Secret Manager Docs**: [cloud.google.com/secret-manager/docs](https://cloud.google.com/secret-manager/docs)
- **Pricing**: [cloud.google.com/secret-manager/pricing](https://cloud.google.com/secret-manager/pricing)
- **IAM Roles**: [cloud.google.com/secret-manager/docs/access-control](https://cloud.google.com/secret-manager/docs/access-control)
- **HERMES Support**: info@parallax-ai.app

---

**Last Updated**: 2024-11-19
