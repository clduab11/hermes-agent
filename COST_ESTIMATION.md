# HERMES Cost Estimation

This document provides a detailed breakdown of monthly costs for running HERMES in production on Google Cloud Platform.

---

## 📊 Executive Summary

| Deployment Type | Monthly Cost | Use Case |
|-----------------|--------------|----------|
| **Demo/Development** | $105-$205 | Testing, proof-of-concept |
| **Production (Standard)** | $455-$815 | Small-medium law firms (10-50 users) |
| **Production (High-Traffic)** | $815-$1,440+ | Large law firms (50+ users, high usage) |

**Cost Drivers**:
1. GCP App Engine compute (largest expense)
2. OpenAI API usage (variable with usage)
3. Supabase database (scales with data)
4. Stripe transaction fees (percentage-based)

---

## 🔵 Demo/Development Configuration

**Best for**: Initial testing, development, proof-of-concept

### Infrastructure Costs

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| **GCP App Engine** | 1 CPU, 2GB RAM, 1-10 instances | $50-100 |
| **Supabase** | Free tier (500MB, 2GB bandwidth) | $0 |
| **OpenAI API** | Light testing (~50K tokens/day) | $50-100 |
| **Stripe** | Test mode | $0 |
| **GCP Secret Manager** | 10 secrets, minimal access | $5 |
| **Redis** | Skip (optional) | $0 |
| **VPC Connector** | Skip (optional) | $0 |

**Total**: **$105-$205/month**

### Usage Assumptions
- 100-500 requests/day
- 10-20 concurrent users max
- Test/development workload
- Cold starts acceptable (5-10s)
- No 24/7 availability requirement

### Cost Optimization Tips
- Use `app.yaml.demo` configuration
- Skip Redis (use in-memory fallback)
- Skip VPC connector (use public URLs)
- Use Supabase free tier
- Keep OpenAI usage low (limit testing)
- Set usage limits on all services

---

## 🟢 Production (Standard) Configuration

**Best for**: Small-medium law firms, 10-50 concurrent users

### Infrastructure Costs

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| **GCP App Engine** | 2 CPU, 4GB RAM, 3-50 instances | $150-300 |
| **Supabase Pro** | 8GB storage, 50GB bandwidth | $100-150 |
| **OpenAI API** | Moderate usage (~1-3M tokens/month) | $100-300 |
| **Stripe Fees** | 2.9% + $0.30 per transaction | $50-150 |
| **GCP Secret Manager** | 10 secrets, moderate access | $10 |
| **Redis (GCP Memorystore)** | 1GB Basic tier | $50 |
| **VPC Connector** | Standard configuration | $30 |
| **Cloud Logging** | Standard retention | $5-15 |

**Total**: **$455-$815/month**

### Usage Assumptions
- 1,000-5,000 requests/day
- 10-50 concurrent users
- 95% uptime target
- <2s response time
- 24/7 availability

### ROI Analysis

**Monthly Revenue** (1 client at $2,497):
- Gross revenue: $2,497
- Stripe fees: -$72
- Infrastructure: -$600 (avg)
- **Net margin**: $1,825 (73%)

**Break-even**: ~0.3 clients

---

## 🔴 Production (High-Traffic) Configuration

**Best for**: Large law firms, 50+ concurrent users, high-volume usage

### Infrastructure Costs

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| **GCP App Engine** | 4 CPU, 8GB RAM, 5-100 instances | $300-480 |
| **Supabase Pro+** | 50GB storage, 200GB bandwidth | $150-250 |
| **OpenAI API** | High usage (~5-10M tokens/month) | $500-1,000 |
| **Stripe Fees** | 2.9% + $0.30 per transaction | $150-300 |
| **GCP Secret Manager** | 20 secrets, high access | $65 |
| **Redis (GCP Memorystore)** | 5GB Standard tier (HA) | $150 |
| **VPC Connector** | High-throughput configuration | $50 |
| **Cloud Logging** | Extended retention | $20-30 |
| **Cloud Monitoring** | Custom dashboards, alerts | $10-20 |

**Total**: **$815-$1,440+/month**

### Usage Assumptions
- 10,000+ requests/day
- 50-200 concurrent users
- 99.9% uptime SLA
- <500ms response time
- High availability (multi-region future)

### ROI Analysis

**Monthly Revenue** (5 clients at $2,497):
- Gross revenue: $12,485
- Stripe fees: -$360
- Infrastructure: -$1,200 (avg)
- **Net margin**: $10,925 (87%)

**Break-even**: ~0.5 clients

---

## 💰 Detailed Cost Breakdown

### 1. Google Cloud App Engine

**Pricing Model**: Pay per instance-hour

| Configuration | Cost/hour | Cost/month (730hrs) |
|---------------|-----------|---------------------|
| 1 CPU, 2GB RAM | ~$0.07 | ~$50 (1 instance) |
| 2 CPU, 4GB RAM | ~$0.14 | ~$100 (1 instance) |
| 4 CPU, 8GB RAM | ~$0.28 | ~$200 (1 instance) |

**Scaling Impact**:
- **Min instances**: Always-on instances (eliminate cold starts)
- **Max instances**: Burst capacity for traffic spikes
- **Auto-scaling**: Charges only for active instances

**Example Calculation** (Production Standard):
- Min instances: 3 × $100 = $300/month (always on)
- Peak scaling: 2 hours/day × 5 extra instances × $100/730hrs = $14/month
- **Total**: ~$314/month

### 2. Supabase Database

**Pricing Tiers**:

| Plan | Storage | Bandwidth | Monthly Cost |
|------|---------|-----------|--------------|
| **Free** | 500MB | 2GB | $0 |
| **Pro** | 8GB + $0.125/GB | 50GB + $0.09/GB | $25 base |
| **Team** | 100GB + $0.125/GB | 250GB + $0.09/GB | $599 base |

**Usage-Based Charges**:
- Storage overage: $0.125 per GB/month
- Bandwidth overage: $0.09 per GB

**Example Calculation** (Production Standard):
- Base: $25/month
- Storage: 15GB = (15-8) × $0.125 = $0.88
- Bandwidth: 75GB = (75-50) × $0.09 = $2.25
- **Total**: ~$28/month

### 3. OpenAI API

**Model Pricing**:

| Model | Input (per 1K tokens) | Output (per 1K tokens) |
|-------|-----------------------|------------------------|
| GPT-4 | $0.03 | $0.06 |
| GPT-4 Turbo | $0.01 | $0.03 |
| GPT-3.5 Turbo | $0.0005 | $0.0015 |
| Whisper | $0.006 per minute of audio |

**Per-Interaction Cost**:
- Input: ~500 tokens = $0.015 (GPT-4)
- Output: ~300 tokens = $0.018 (GPT-4)
- Voice: ~3 min = $0.018 (Whisper)
- **Total per call**: ~$0.05

**Monthly Estimates**:
- 1,000 interactions: $50
- 5,000 interactions: $250
- 10,000 interactions: $500
- 50,000 interactions: $2,500

**Optimization**:
- Use GPT-3.5 Turbo for simple tasks (30x cheaper)
- Cache common responses (80% hit rate possible)
- Reduce max_tokens to limit output length
- Batch requests when possible

### 4. Stripe Payment Processing

**Pricing**: 2.9% + $0.30 per successful charge

**Examples**:
- $2,497 plan: $72.41 + $0.30 = $72.71 fee
- $100 overage: $2.90 + $0.30 = $3.20 fee

**Monthly Volume**:
- 1 client: ~$73/month
- 5 clients: ~$365/month
- 10 clients: ~$730/month

**Note**: No monthly fees, only transaction fees

### 5. GCP Secret Manager

**Pricing**:
- Secret version: $0.06 per version/month (6 free)
- Access operations: $0.03 per 10,000 accesses

**Example Calculation**:
- Secrets: 10 versions = (10-6) × $0.06 = $0.24
- Accesses: 20M/month = 20M/10K × $0.03 = $60
- **Total**: ~$60-65/month

**Optimization**: HERMES caches secrets, reducing access count by 95%

### 6. Redis Cache (GCP Memorystore)

**Pricing**:

| Tier | Size | Monthly Cost |
|------|------|--------------|
| **Basic** (1GB) | No HA | $50 |
| **Standard** (1GB) | With HA | $150 |
| **Basic** (5GB) | No HA | $250 |

**Optional but Recommended**:
- Skip for dev/demo (use in-memory)
- Basic tier for production standard
- Standard tier for high-traffic

### 7. VPC Connector

**Pricing**:
- Connector: ~$30/month
- Data processing: $0.12 per GB

**Example**:
- 100GB data transfer: 100 × $0.12 = $12
- **Total**: ~$42/month

**Optional**: Skip if using public endpoints

---

## 📉 Cost Optimization Strategies

### 1. Start Small, Scale Up

**Phase 1: Demo** ($105-205/month)
- Use app.yaml.demo
- Skip Redis and VPC
- Supabase free tier
- Minimal OpenAI testing

**Phase 2: Initial Production** ($455-615/month)
- Add Redis (Basic tier)
- Upgrade Supabase to Pro
- Keep moderate OpenAI usage
- Monitor and optimize

**Phase 3: Scale as Needed** ($815-1440/month)
- Add VPC for security
- Increase Redis capacity
- Higher OpenAI limits
- Multi-region (future)

### 2. Service-Specific Optimizations

**GCP App Engine**:
- ✅ Use min_instances wisely (balance cost vs cold starts)
- ✅ Set appropriate max_instances (prevent runaway costs)
- ✅ Use app.yaml.demo for non-production
- ❌ Don't over-provision CPU/memory

**OpenAI API**:
- ✅ Cache responses (Redis or in-memory)
- ✅ Use GPT-3.5 for simple tasks
- ✅ Set max_tokens limit
- ✅ Implement request deduplication
- ❌ Don't use GPT-4 for everything

**Supabase**:
- ✅ Monitor storage growth
- ✅ Archive old conversations
- ✅ Use connection pooling
- ✅ Optimize queries
- ❌ Don't store unnecessary data

**Stripe**:
- ✅ Consider ACH when possible (0.8% vs 2.9%)
- ✅ Clear billing descriptors (reduce disputes)
- ✅ Implement retry logic (reduce failed payments)

### 3. Monitoring & Alerts

Set budget alerts:
- **50% of budget**: Warning alert
- **80% of budget**: Critical alert
- **100% of budget**: Service pause consideration

**GCP Budget Alert Setup**:
```bash
gcloud billing budgets create \
    --billing-account=BILLING_ACCOUNT_ID \
    --display-name="HERMES Monthly Budget" \
    --budget-amount=1000 \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=80 \
    --threshold-rule=percent=100
```

---

## 🎯 Pricing Strategy Alignment

### Enterprise Plan: $2,497/month

**Cost Structure**:
- Infrastructure: $600-1,200 (25-48%)
- Gross margin: $1,300-1,900 (52-75%)

**Client Break-even Analysis**:
- 1 client: Profitable ($1,825 margin)
- 2 clients: High margin ($4,650 margin)
- 5+ clients: Excellent margin ($10,925+ margin)

**Overage Pricing**: $0.25/interaction
- Cost: ~$0.05 (OpenAI)
- Margin: $0.20 (80% margin)

---

## 🚨 Cost Risk Mitigation

### Potential Cost Overruns

| Risk | Impact | Mitigation |
|------|--------|------------|
| **OpenAI API spike** | High ($1000+) | Set hard limits, implement caching |
| **App Engine runaway** | High ($500+) | Set max_instances, monitor alerts |
| **Stripe disputes** | Medium ($15/dispute) | Clear billing descriptors |
| **Data transfer** | Low ($50-100) | Use VPC, optimize bandwidth |

### Safety Measures

1. **Hard Limits**:
   - OpenAI: $1,000/month max
   - App Engine: 100 max instances
   - Supabase: Alert at 80% quota

2. **Monitoring**:
   - Daily cost review
   - Weekly budget reconciliation
   - Monthly optimization review

3. **Fallbacks**:
   - GPT-3.5 Turbo if GPT-4 budget exceeded
   - Scale down App Engine if needed
   - Cached responses when possible

---

## 📞 Support

Questions about costs?
- **GCP Billing**: [cloud.google.com/billing/docs](https://cloud.google.com/billing/docs)
- **Cost Calculator**: [cloud.google.com/products/calculator](https://cloud.google.com/products/calculator)
- **HERMES Support**: info@parallax-ai.app

---

**Last Updated**: 2024-11-19

**Disclaimer**: Costs are estimates based on typical usage patterns. Actual costs may vary based on usage, region, and service pricing changes. Monitor actual costs in GCP Billing Console.
