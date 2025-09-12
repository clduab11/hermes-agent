
# HERMES Deployment Guide

## Google Cloud Platform Deployment

### Prerequisites

1. Google Cloud SDK installed and configured
2. Docker installed
3. HERMES repository cloned
4. Environment variables configured

### Step 1: Build Docker Image

```bash
# Build production Docker image
docker build -t hermes-ai-voice-agent .

# Tag for Google Container Registry
docker tag hermes-ai-voice-agent gcr.io/YOUR_PROJECT_ID/hermes-ai-voice-agent
```

### Step 2: Push to Container Registry

```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Push image
docker push gcr.io/YOUR_PROJECT_ID/hermes-ai-voice-agent
```

### Step 3: Deploy to Cloud Run

```bash
gcloud run deploy hermes-voice-agent \
  --image gcr.io/YOUR_PROJECT_ID/hermes-ai-voice-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --concurrency 80 \
  --max-instances 10 \
  --set-env-vars "OPENAI_API_KEY=your-key,SUPABASE_URL=your-url"
```

### Step 4: Configure Custom Domain

```bash
gcloud run domain-mappings create \
  --service hermes-voice-agent \
  --domain your-domain.com \
  --region us-central1
```

## Environment Configuration

### Production Environment Variables

```bash
# Core Configuration
API_HOST=0.0.0.0
API_PORT=8080
DEBUG=false

# AI Services
OPENAI_API_KEY=your-openai-key
WHISPER_MODEL=base
KOKORO_API_URL=your-tts-service-url

# MCP Integration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
MEM0_API_KEY=your-mem0-key
GITHUB_TOKEN=your-github-token

# Security
JWT_PRIVATE_KEY=your-private-key
JWT_PUBLIC_KEY=your-public-key
CONFIDENCE_THRESHOLD=0.90

# Performance
MAX_AUDIO_LENGTH_SECONDS=30
RESPONSE_TIMEOUT_SECONDS=0.1
```

## Monitoring and Observability

### Health Checks

Cloud Run automatically monitors:
- `/health` endpoint for container health
- Response time and error rates
- Memory and CPU usage

### Logging

```bash
# View application logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=hermes-voice-agent"
```

### Metrics

Key metrics to monitor:
- Voice processing latency (<100ms target)
- Total response time (<500ms target)
- Concurrent connections
- Error rates
- Cache hit ratios

## Scaling Configuration

### Automatic Scaling

```yaml
# cloud-run-config.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  annotations:
    run.googleapis.com/execution-environment: gen2
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "100"
        run.googleapis.com/cpu: "2"
        run.googleapis.com/memory: "2Gi"
```

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test voice synthesis endpoint
ab -n 1000 -c 10 -H "Content-Type: application/json" \
  -p test-payload.json \
  https://your-domain.com/test/synthesize
```

## Security Considerations

### TLS Configuration

Cloud Run provides automatic TLS termination with managed certificates.

### Authentication

- JWT tokens with RS256 signing
- Tenant isolation at database level
- API rate limiting (100 requests/minute per IP)

### Compliance

- All communications encrypted with TLS 1.3
- Audit logging enabled for all API calls
- 90-day data retention policy
- HIPAA and GDPR compliance measures

## Troubleshooting

### Common Issues

1. **Cold Start Latency**
   - Ensure minimum instances set to 1
   - Pre-warm connections in startup

2. **Memory Issues**
   - Monitor Whisper model memory usage
   - Increase Cloud Run memory allocation

3. **Timeout Errors**
   - Increase Cloud Run timeout to 300 seconds
   - Optimize AI service response times

### Debug Commands

```bash
# Check service status
gcloud run services describe hermes-voice-agent --region us-central1

# View recent logs  
gcloud logging read --limit 50 "resource.type=cloud_run_revision"

# Connect to service for debugging
gcloud run services proxy hermes-voice-agent --port 8080
```
        