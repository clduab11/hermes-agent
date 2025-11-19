# OpenAI API Setup Guide

This guide walks you through setting up OpenAI API for AI and voice features in HERMES.

---

## Overview

HERMES uses OpenAI API for:
- **GPT-4**: Legal reasoning, response generation, client intake
- **Whisper**: Speech-to-text (STT) for voice calls
- **Text Generation**: Legal document drafting assistance
- **Embeddings**: Semantic search (optional, future feature)

**Reference Code**: `hermes/ai/openai_service.py`

---

## Step 1: Create OpenAI Account

1. Go to [platform.openai.com](https://platform.openai.com/)
2. Click "Sign up" or "Get started"
3. Sign up with:
   - Email (verify email address)
   - Google account
   - Microsoft account
4. Complete profile setup

---

## Step 2: Request GPT-4 Access

GPT-4 access is **required** for production HERMES deployment.

### Check Current Access

1. Go to [platform.openai.com/account/limits](https://platform.openai.com/account/limits)
2. Look for "GPT-4" in the model list
3. Check if you have access (RPM > 0)

### Request Access (if needed)

If you don't have GPT-4 access:

1. Add a payment method (see Step 3)
2. Make a small purchase (buy $5-10 credits)
3. Wait 24-48 hours for automatic approval
4. Check limits again

**Alternative**: Contact OpenAI support to request access faster (usually approved within 1-2 business days for legitimate use cases).

---

## Step 3: Add Payment Method

1. Go to [platform.openai.com/account/billing](https://platform.openai.com/account/billing)
2. Click "Add payment method"
3. Enter credit/debit card details
4. Set up billing preferences:
   - **Auto-recharge**: Enable (recommended)
   - **Recharge amount**: $100-500
   - **Recharge threshold**: $10-50

---

## Step 4: Set Usage Limits

Prevent unexpected charges by setting usage limits.

### Hard Limit

1. Go to [platform.openai.com/account/limits](https://platform.openai.com/account/limits)
2. Click "Set limit" under "Usage limits"
3. Set monthly limit (recommended):
   - **Development**: $100/month
   - **Production**: $500-1000/month
   - **High-traffic**: $1000-5000/month
4. Click "Save"

### Soft Limit (Email Alert)

1. In the same page, set "Email notification threshold"
2. Recommended: 50% of hard limit
3. You'll receive email when reached

---

## Step 5: Generate API Key

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Configure key:
   - **Name**: `HERMES Production` (or descriptive name)
   - **Permissions**: All (or restrict if needed)
4. Click "Create secret key"
5. **Copy the key immediately** (starts with `sk-...`)
   - ⚠️ You won't be able to see it again!
6. Store in `.env`:
   ```bash
   OPENAI_API_KEY=sk-your-api-key-here
   ```

### API Key Security

- ✅ Never commit to git
- ✅ Store in environment variables
- ✅ Use GCP Secret Manager for production
- ✅ Rotate keys periodically
- ❌ Never expose in frontend code
- ❌ Never log API keys

---

## Step 6: Configure HERMES Environment

Add to your `.env` file:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-api-key-here

# Model Selection
OPENAI_MODEL=gpt-4  # or gpt-4-turbo, gpt-3.5-turbo

# Optional: Organization ID (if using organization account)
# OPENAI_ORG_ID=org-your-org-id-here

# Request Configuration
OPENAI_MAX_TOKENS=1000  # Max tokens per response
OPENAI_TEMPERATURE=0.7  # 0.0-1.0, lower = more deterministic

# Whisper Configuration (for STT)
WHISPER_MODEL=base  # Options: tiny, base, small, medium, large
WHISPER_DEVICE=cpu  # or cuda if GPU available
```

---

## Step 7: Test API Access

### Using curl

```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

Expected response: List of available models

### Using Python

```python
import openai

openai.api_key = "sk-your-api-key-here"

# Test models endpoint
models = openai.models.list()
print("Available models:", [m.id for m in models.data if 'gpt-4' in m.id])

# Test chat completion
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful legal assistant."},
        {"role": "user", "content": "What is attorney-client privilege?"}
    ],
    max_tokens=100
)
print("Response:", response.choices[0].message.content)
```

---

## Step 8: Understand Rate Limits

Rate limits vary by tier (based on total spending):

### Tier Structure

| Tier | Total Spent | GPT-4 RPM | GPT-4 TPM | GPT-3.5 RPM |
|------|-------------|-----------|-----------|-------------|
| Free | $0 | 3 | 40,000 | 3 |
| Tier 1 | $5+ | 500 | 40,000 | 3,500 |
| Tier 2 | $50+ | 5,000 | 300,000 | 3,500 |
| Tier 3 | $100+ | 5,000 | 300,000 | 3,500 |
| Tier 4 | $250+ | 10,000 | 600,000 | 10,000 |
| Tier 5 | $1,000+ | 10,000 | 2,000,000 | 10,000 |

**RPM**: Requests per minute
**TPM**: Tokens per minute

### Production Recommendation

- **Minimum**: Tier 3 ($100+ spent) for reliable production use
- **Optimal**: Tier 4 ($250+ spent) for high-traffic deployments

### Check Your Current Tier

```bash
curl https://api.openai.com/v1/usage \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## Step 9: Cost Estimation

### Token-Based Pricing

| Model | Input (per 1K tokens) | Output (per 1K tokens) |
|-------|-----------------------|------------------------|
| GPT-4 | $0.03 | $0.06 |
| GPT-4 Turbo | $0.01 | $0.03 |
| GPT-3.5 Turbo | $0.0005 | $0.0015 |
| Whisper | $0.006 per minute |

### HERMES Usage Estimates

**Per Client Interaction** (average):
- Input: ~500 tokens (context + user query)
- Output: ~300 tokens (assistant response)
- **Cost per interaction**: $0.015 + $0.018 = $0.033

**Monthly Estimates**:
- **1,000 interactions**: $33
- **10,000 interactions**: $330
- **50,000 interactions**: $1,650

**Voice Processing** (Whisper):
- Average call: 3-5 minutes
- Cost per call: ~$0.02-0.03
- Negligible compared to GPT-4

---

## Step 10: Optimize Usage & Costs

### Reduce Token Usage

```python
# 1. System prompt optimization
# Bad: Long, verbose system prompt
system_prompt = """You are an advanced AI legal assistant..."""  # 500 tokens

# Good: Concise, focused prompt
system_prompt = "Legal AI assistant. Provide accurate, compliant responses."  # 50 tokens

# 2. Use max_tokens to limit responses
response = openai.chat.completions.create(
    model="gpt-4",
    messages=messages,
    max_tokens=300  # Prevent overly long responses
)

# 3. Truncate conversation history
# Keep only last N messages instead of full conversation
messages = messages[-6:]  # Last 3 exchanges (user + assistant)
```

### Caching & Deduplication

```python
# Cache common responses (in Redis or in-memory)
import hashlib

def get_cached_response(prompt):
    cache_key = hashlib.md5(prompt.encode()).hexdigest()
    cached = redis.get(f"gpt_response:{cache_key}")
    if cached:
        return cached
    return None

def cache_response(prompt, response):
    cache_key = hashlib.md5(prompt.encode()).hexdigest()
    redis.setex(f"gpt_response:{cache_key}", 3600, response)  # Cache 1 hour
```

### Use Cheaper Models When Appropriate

```python
# Simple classification: Use GPT-3.5 Turbo
if task_type == "classification":
    model = "gpt-3.5-turbo"  # 30x cheaper than GPT-4
else:
    model = "gpt-4"  # Use for complex reasoning
```

### Batch Requests

```python
# Instead of: 10 separate API calls
for query in queries:
    response = openai.chat.completions.create(...)

# Better: 1 batched call
combined_query = "\n".join(queries)
response = openai.chat.completions.create(...)
```

---

## Troubleshooting

### Issue: Rate Limit Exceeded

**Error**: `openai.error.RateLimitError: Rate limit reached`

**Solutions**:
- Wait and retry (rate limits reset every minute)
- Implement exponential backoff
- Upgrade to higher tier (spend more to increase limits)
- Reduce request frequency
- Use batch requests

**Retry Logic**:
```python
import time
from openai import OpenAI

client = OpenAI()

def call_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except openai.RateLimitError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
            else:
                raise
```

### Issue: Insufficient Quota

**Error**: `You exceeded your current quota`

**Solutions**:
- Add payment method
- Increase usage limit
- Purchase more credits
- Wait for monthly quota reset (if on free tier)

### Issue: Model Not Found

**Error**: `The model 'gpt-4' does not exist`

**Solutions**:
- Verify you have GPT-4 access
- Check spelling: `gpt-4`, not `gpt4` or `GPT-4`
- Use `gpt-3.5-turbo` as fallback for testing

### Issue: API Key Invalid

**Error**: `Incorrect API key provided`

**Solutions**:
- Verify key starts with `sk-`
- Check for extra spaces or newlines
- Regenerate key if lost
- Ensure key is from correct account/organization

---

## Error Handling Best Practices

```python
from openai import OpenAI, OpenAIError, RateLimitError, APITimeoutError

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def safe_completion(messages, model="gpt-4"):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1000,
            timeout=30  # 30 second timeout
        )
        return response.choices[0].message.content
    
    except RateLimitError:
        # Retry with backoff or return cached response
        return "Rate limit exceeded. Please try again."
    
    except APITimeoutError:
        # Request timed out
        return "Request timed out. Please try again."
    
    except OpenAIError as e:
        # Other OpenAI errors
        print(f"OpenAI Error: {e}")
        return "AI service temporarily unavailable."
    
    except Exception as e:
        # Unexpected errors
        print(f"Unexpected error: {e}")
        return "An error occurred. Please try again."
```

---

## Monitoring Usage

### Via OpenAI Dashboard

1. Go to [platform.openai.com/usage](https://platform.openai.com/usage)
2. View:
   - Daily usage (tokens, requests, cost)
   - Model breakdown
   - Historical trends

### Via API

```python
# Get current usage
usage = openai.usage.retrieve()
print(f"Total cost this month: ${usage.total_usage / 100}")
```

### Set Up Alerts

1. Go to [platform.openai.com/account/limits](https://platform.openai.com/account/limits)
2. Enable email notifications at:
   - 50% of monthly limit
   - 80% of monthly limit
   - 100% of monthly limit

---

## Advanced Configuration

### Organization ID

If using an organization account:

```bash
# Add to .env
OPENAI_ORG_ID=org-your-org-id-here
```

```python
# Use in code
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    organization=os.getenv("OPENAI_ORG_ID")
)
```

### Proxy Configuration

If behind corporate proxy:

```python
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=httpx.Client(proxies="http://proxy.company.com:8080")
)
```

### Custom Timeout

```python
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=60.0  # 60 seconds
)
```

---

## Compliance & Data Privacy

### Data Retention

- **API Data**: Not used for training as of March 2023
- **Retention**: 30 days for abuse monitoring, then deleted
- **Zero Data Retention (ZDR)**: Available for enterprise (contact sales)

### GDPR Compliance

- OpenAI is GDPR compliant
- Data Processing Agreement (DPA) available
- Users have right to deletion

### HIPAA Compliance

- Not HIPAA compliant by default
- Business Associate Agreement (BAA) available for enterprise
- Contact OpenAI sales for healthcare use cases

**Note**: For legal AI, attorney-client privilege considerations may apply. Consult legal counsel.

---

## Next Steps

Once OpenAI API is configured:

1. ✅ Test API key with curl or Python
2. ✅ Verify GPT-4 access
3. ✅ Set usage limits ($500/month recommended)
4. ✅ Configure `.env` with API key
5. ✅ Test HERMES AI features locally
6. ✅ Continue with deployment: [DEPLOYMENT.md](../../DEPLOYMENT.md)

---

## Support

- **OpenAI Docs**: [platform.openai.com/docs](https://platform.openai.com/docs)
- **API Reference**: [platform.openai.com/docs/api-reference](https://platform.openai.com/docs/api-reference)
- **OpenAI Support**: [help.openai.com](https://help.openai.com/)
- **Community**: [community.openai.com](https://community.openai.com/)
- **HERMES Support**: info@parallax-ai.app

---

**Last Updated**: 2024-11-19
