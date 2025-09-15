# HERMES Deployment Guide

## Quick Start Options

### Option 1: One-Click Cloud Deployment (Recommended)

Deploy the backend to enable full voice functionality:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/clduab11/hermes-agent)

1. Click "Deploy to Render" button above
2. Set your OpenAI API key (get from https://platform.openai.com/)
3. Deploy (takes ~5-10 minutes)
4. Copy the deployed URL to connect with the frontend

**Cost**: Free tier available (sleeps after inactivity, perfect for demos)

### Option 2: Local Development

For local development and testing:

1. **Prerequisites**: Docker and docker-compose
2. **Clone**: `git clone https://github.com/clduab11/hermes-agent.git`
3. **Configure**: Copy `.env.example` to `.env` and add your API keys
4. **Run**: `docker-compose up` to start frontend and backend services
5. **Access**: Demo at http://localhost:5173, Backend API at http://localhost:8000

### Option 3: Railway.app Deployment

Alternative cloud deployment with excellent developer experience:

1. Install Railway CLI: `npm install -g @railway/cli`
2. Clone this repository and navigate to it
3. Run `railway login` and `railway up`
4. Set environment variables: `railway variables set OPENAI_API_KEY=your_key_here`
5. App deploys automatically

## Connecting GitHub Pages Demo to Your Backend

After deploying your backend, connect it to the GitHub Pages demo:

1. **Fork this repository**
2. **Go to Settings → Secrets and variables → Actions** in your fork
3. **Add these repository secrets**:
   ```
   VITE_BACKEND_URL: https://your-hermes-app.onrender.com
   VITE_BACKEND_WS_URL: wss://your-hermes-app.onrender.com
   VITE_ENVIRONMENT: production
   ```
4. **Push any change** to trigger GitHub Pages rebuild
5. **Visit your GitHub Pages URL** - now has full voice functionality!

## Architecture

```
GitHub Pages (Frontend)  →  Cloud Backend  →  AI Services
- React App                 - FastAPI        - OpenAI API
- WebSocket Client          - WebSocket      - Whisper STT  
- Voice Interface           - Voice Pipeline - GPT-4 LLM
```

## Documentation

- **Complete Deployment Guide**: `docs/deployment.md`
- **Clio OAuth Setup**: `docs/clio-setup.md`
- **Supabase Integration**: `docs/supabase-setup.md`

## Production Configuration

For production deployments:
- Set `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` for database features
- Set `CLIO_CLIENT_ID`, `CLIO_CLIENT_SECRET`, `CLIO_REDIRECT_URI` for CRM integration
- Configure `CORS_ALLOW_ORIGINS` and disable `DEMO_MODE`
- Enable monitoring and proper security settings

This setup provides enterprise-grade voice processing suitable for legal technology demonstrations.
