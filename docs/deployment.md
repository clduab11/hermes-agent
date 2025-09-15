
# HERMES Backend Deployment Guide

This guide explains how to deploy the HERMES backend to make the GitHub Pages demo fully functional with voice transcription and TTS capabilities.

## Current Status

The HERMES demo at https://clduab11.github.io/hermes-agent/ currently runs in "demo mode" because it only serves static files through GitHub Pages. To enable full functionality, you need to deploy the Python FastAPI backend to a cloud service.

## Quick Deploy Options

### Option 1: Render.com (Recommended for Demo)

Render offers a generous free tier perfect for demonstrations:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/clduab11/hermes-agent)

**Steps:**
1. Click the "Deploy to Render" button above
2. Connect your GitHub account and fork the repository  
3. Set your OpenAI API key in the environment variables
4. Deploy (takes ~5-10 minutes)
5. Copy the deployed URL and update the frontend configuration

**Free Tier Limits:**
- 512MB RAM, shared CPU
- Sleeps after 15 minutes of inactivity  
- 750 build hours/month
- Perfect for demonstrations and testing

### Option 2: Railway.app 

Railway offers $5/month credit and excellent developer experience:

1. Install Railway CLI: `npm install -g @railway/cli`
2. Clone and navigate to this repository
3. Run `railway login` and `railway up`
4. Set environment variables: `railway variables set OPENAI_API_KEY=your_key_here`
5. Your app will be deployed automatically

### Option 3: Local Development with Docker

For local development and testing:

1. Clone the repository
2. Copy `.env.example` to `.env` and set your API keys
3. Run `docker-compose up` to start frontend and backend services
4. Access the demo at http://localhost:5173
5. Backend API available at http://localhost:8000

## Required Environment Variables

For any deployment, you'll need:

```bash
# Required
OPENAI_API_KEY=sk-...  # Get from https://platform.openai.com/

# Recommended for production
CORS_ALLOW_ORIGINS=https://clduab11.github.io  # Allow GitHub Pages
DEMO_MODE=true  # Enable demo features
WHISPER_MODEL=tiny  # Use smallest model for better performance
CONFIDENCE_THRESHOLD=0.7  # Lower threshold for demo
```

## Connecting Frontend to Deployed Backend

After deploying your backend, you need to update the frontend to connect to it:

### Method 1: Update GitHub Pages Deployment

1. Fork this repository
2. Go to your repository settings → Secrets and variables → Actions  
3. Add repository secrets:
   ```
   VITE_BACKEND_WS_URL: wss://your-hermes-app.onrender.com
   VITE_BACKEND_URL: https://your-hermes-app.onrender.com
   VITE_ENVIRONMENT: production
   ```
4. Push a change to trigger GitHub Pages rebuild
5. Your demo will now connect to the backend!

## Deployment Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  GitHub Pages   │────▶│  Cloud Backend   │────▶│  External APIs  │
│  (Static Site)  │     │  (Render/Railway)│     │                 │
│                 │     │                 │     │  - OpenAI API   │
│  - React App    │     │  - FastAPI      │     │  - Whisper STT  │
│  - WebSocket    │     │  - WebSocket    │     │  - GPT-4 LLM    │
│    Client       │     │  - Voice Pipeline│     │  - TTS Service  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Testing Your Deployment

1. Visit your deployed backend URL + `/health` (e.g., `https://your-app.onrender.com/health`)
2. You should see: `{"status": "healthy", "timestamp": "..."}`
3. Visit the GitHub Pages demo: https://clduab11.github.io/hermes-agent/
4. Click "Try Voice Demo" and "Start Voice Input"
5. You should see "✅ Connected to HERMES voice processing backend"

## Integration Documentation

- Clio OAuth Setup: `docs/clio-setup.md`
- Supabase Integration: `docs/supabase-setup.md`

## Production Notes

- Set `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` for database-backed features
- Set `CLIO_CLIENT_ID`, `CLIO_CLIENT_SECRET`, `CLIO_REDIRECT_URI` for Clio integration
- Restrict CORS via `CORS_ALLOW_ORIGINS` and disable demo mode in production
- Monitor API usage costs (OpenAI, TTS services)
- Consider rate limiting for public deployments

## Google Cloud Platform Deployment (Advanced)

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
        