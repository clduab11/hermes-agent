# HERMES Environment Variables

This document consolidates all environment variables used across the repository and explains when to set them.

- Never commit real secrets. Use a local `.env` for development and a secret manager in production.
- See [.env.example](../.env.example) for a ready-to-copy template.

## Core (Required to run LLM)
- `OPENAI_API_KEY` (required): OpenAI API key for LLM and certain TTS features.
- `OPENAI_MODEL` (default: `gpt-4`): Model selection.

## Server & Audio (non-secrets)
- `API_HOST` (default: `0.0.0.0`)  
- `API_PORT` (default: `8000`)  
- `DEBUG` (default: `true`)  
- `WHISPER_MODEL` (default: `base`)  
- `WHISPER_DEVICE` (default: `cpu`)  
- `KOKORO_API_URL` (default: `http://localhost:8001`)  
- `KOKORO_VOICE` (default: `af_sarah`)  
- `SAMPLE_RATE` (default: `16000`)  
- `CHUNK_SIZE` (default: `1024`)  
- `MAX_AUDIO_LENGTH_SECONDS` (default: `30`)  
- `RESPONSE_TIMEOUT_SECONDS` (default: `0.1`)  
- `CONFIDENCE_THRESHOLD` (default: `0.85`)  
- `ENABLE_DISCLAIMERS` (default: `true`)  
- `AUDIT_LOGGING` (default: `true`)

## Authentication (JWT)
- `JWT_PRIVATE_KEY` (optional, PEM, single line with `\n` escapes): Required to mint RS256 access/refresh tokens.
- `JWT_PUBLIC_KEY` (optional, PEM): Required to verify tokens.

## Data Stores
- `DATABASE_URL` (optional): PostgreSQL URL for persistence (e.g., Supabase). Required for DB-backed features.
- `REDIS_URL` (optional): Redis URL for caching/state.
  - Local: `redis://localhost:6379`
  - Docker: `redis://redis:6379`

## MCP Integrations
- GitHub
  - `GITHUB_TOKEN` (optional): Fine-grained PAT for repo automation.
- Supabase (only if using Supabase MCP server/REST)
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_ROLE_KEY` (server-side only)
- Mem0 (contextual memory via hosted API)
  - `MEM0_API_KEY` (required if using hosted Mem0 API)
- Clio (OAuth for CRM automation)
  - `CLIO_CLIENT_ID`, `CLIO_CLIENT_SECRET`, `CLIO_REDIRECT_URI`
- Zapier
  - Webhooks: `ZAPIER_WEBHOOK_CLIENT_INTAKE`, `ZAPIER_WEBHOOK_MATTER_UPDATE`, `ZAPIER_WEBHOOK_APPOINTMENT_SCHEDULED`
  - Direct API: `ZAPIER_API_KEY` (only if calling Zapier APIs beyond webhooks)

## Billing / Payments
- Stripe (Stripe Link is part of Stripe; uses the same Stripe API keys)
  - `STRIPE_API_KEY`
  - `STRIPE_WEBHOOK_SECRET`
  - `STRIPE_PRICE_PRO`, `STRIPE_PRICE_ENTERPRISE`, `STRIPE_OVERAGE_PRICE`
- Plaid Link (not implemented by default; add only if you integrate Plaid)
  - `PLAID_CLIENT_ID`, `PLAID_SECRET`, `PLAID_ENV`, `PLAID_WEBHOOK_URL`

## Security Notes
- Do not hardcode secrets in code. Load from env or secret manager.
- Use least-privilege tokens (GitHub PAT, Supabase service role). Never expose service role keys to the client.
- Rotate keys regularly and after any suspected exposure.

## Quick Start
```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY at minimum
python mock_tts_server.py &
python setup_demo.py
python -m hermes.main
```