# Deployment Guide

## Prerequisites
- Docker and docker-compose
- Node.js for local development

## Steps
1. Clone the repository.
2. Run `docker-compose up` to start frontend and backend services.
3. Access the demo at http://localhost:5173.
4. Backend API available at http://localhost:3001.

This setup uses mock services and is intended for demo purposes only.

## Documentation
- Clio OAuth Setup: `docs/clio-setup.md`
- Supabase Integration: `docs/supabase-setup.md`

## Production Notes
- Set `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` for database-backed features.
- Set `CLIO_CLIENT_ID`, `CLIO_CLIENT_SECRET`, `CLIO_REDIRECT_URI` for Clio integration.
- Restrict CORS via `CORS_ALLOW_ORIGINS` and disable demo mode in production.
