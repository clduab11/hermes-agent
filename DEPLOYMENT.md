# HERMES Production Deployment Guide

**Target Audience:** DevOps Engineers, System Administrators  
**Last Updated:** 2025-11-17  
**Production Readiness:** 100%

---

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/clduab11/hermes-agent.git
cd hermes-agent
cp .env.docker.example .env.production

# 2. Edit .env.production with your credentials

# 3. Build and deploy
./scripts/docker-build.sh
./scripts/docker-start.sh production

# 4. Verify deployment
curl https://hermes.yourdomain.com/health
```

## Prerequisites

**System Requirements:**
- 8 CPU cores (minimum 4)
- 32 GB RAM (minimum 16 GB)
- 500 GB SSD storage
- Ubuntu 22.04 LTS
- Docker 24.0+, Docker Compose 2.20+

**Required Accounts:**
- Supabase (database)
- OpenAI API (GPT-4)
- Clio developer account
- Stripe (billing)
- Domain with SSL certificate

## Environment Configuration

See `.env.docker.example` for all variables. Key variables:

```bash
# Database (Supabase recommended)
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.supabase.co:5432/postgres

# OpenAI
OPENAI_API_KEY=sk-[YOUR_KEY]

# Security (generate with openssl)
JWT_PRIVATE_KEY=[RSA_PRIVATE_KEY]
JWT_PUBLIC_KEY=[RSA_PUBLIC_KEY]
SECRET_KEY=[32_CHAR_HEX]
```

## SSL Setup

**Let's Encrypt (Recommended):**
```bash
sudo certbot --nginx -d hermes.yourdomain.com
```

**Self-Signed (Development):**
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem
```

## Deployment

```bash
# Build images
./scripts/docker-build.sh

# Start production
./scripts/docker-start.sh production

# Verify health
curl https://hermes.yourdomain.com/health

# View logs
./scripts/docker-logs.sh api
```

## Scaling

**Horizontal Scaling (Multiple API Instances):**

Update `nginx/conf.d/hermes.conf`:
```nginx
upstream hermes_api {
    least_conn;
    server api1:8000 max_fails=3 fail_timeout=30s;
    server api2:8000 max_fails=3 fail_timeout=30s;
    server api3:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}
```

Update `docker-compose.yml` to add api2, api3 services.

## Backups

**Automated Daily Backups:**
```bash
# Database backup (runs daily at 2 AM)
docker-compose exec -T postgres pg_dump -U postgres hermes | \
  gzip > /backups/hermes-db-$(date +%Y-%m-%d).sql.gz
```

**Restore:**
```bash
gunzip < backup.sql.gz | docker-compose exec -T postgres psql -U postgres hermes
```

## Monitoring

- Health: `https://hermes.yourdomain.com/health`
- Metrics: `http://internal-ip/metrics` (internal only)
- Logs: `./scripts/docker-logs.sh api --follow`

## Troubleshooting

**Database Connection:**
```bash
docker-compose exec postgres pg_isready -U postgres
```

**SSL Issues:**
```bash
docker-compose exec nginx openssl x509 -in /etc/nginx/ssl/cert.pem -noout -dates
```

**High Memory:**
```bash
docker stats
docker-compose restart api
```

## Rollback

```bash
# Stop current
docker-compose down

# Switch to previous version
git checkout v1.0.0

# Redeploy
./scripts/docker-build.sh
./scripts/docker-start.sh production
```

## Support

- GitHub: https://github.com/clduab11/hermes-agent/issues
- Email: support@parallaxanalytics.com

**Status:** ✅ Production Ready
