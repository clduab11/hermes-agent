# HERMES AI Voice Agent - Supabase Deployment Guide

## Production Deployment for Enterprise Law Firms

This guide covers deploying HERMES on Supabase with enterprise-grade security, compliance, and performance optimizations.

## Prerequisites

### Required Services
- **Supabase Project**: PostgreSQL database and authentication
- **Container Registry**: Docker Hub, GitHub Container Registry, or AWS ECR
- **SSL Certificates**: For HTTPS deployment
- **External Redis** (recommended for production scale)

### Required Environment Variables
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
SUPABASE_DATABASE_URL=postgresql://postgres:password@your-project.supabase.co:5432/postgres

# Authentication (Generate RSA keypair)
JWT_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"

# OpenAI Integration
OPENAI_API_KEY=sk-your-openai-api-key

# Security
CORS_ALLOW_ORIGINS=https://your-domain.com,https://admin.your-domain.com
```

## 1. Build and Push Container Image

### Build Production Image
```bash
# Build the production container
docker build -t hermes-ai:latest \
  --target production \
  --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  --build-arg VERSION=1.0.0 \
  .

# Tag for your registry
docker tag hermes-ai:latest your-registry/hermes-ai:latest

# Push to registry
docker push your-registry/hermes-ai:latest
```

### Automated CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build and Push
        run: |
          docker build -t hermes-ai:${GITHUB_SHA} .
          docker push your-registry/hermes-ai:${GITHUB_SHA}

      - name: Deploy to Supabase
        run: |
          # Your deployment commands here
          echo "Deploying HERMES to Supabase..."
```

## 2. Supabase Database Setup

### Create Database Schema
```sql
-- Connect to your Supabase database and run:

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "hstore";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create application-specific schemas
CREATE SCHEMA IF NOT EXISTS hermes;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Grant permissions to authenticated users
GRANT USAGE ON SCHEMA hermes TO authenticated;
GRANT USAGE ON SCHEMA audit TO authenticated;
GRANT USAGE ON SCHEMA analytics TO authenticated;
```

### Run Database Migrations
```bash
# Set your Supabase database URL
export DATABASE_URL="postgresql://postgres:password@your-project.supabase.co:5432/postgres"

# Run Alembic migrations
alembic upgrade head
```

## 3. Container Deployment Options

### Option A: Supabase + External Container Platform

Deploy the container on platforms like:
- **Railway**: Simple deployment with automatic HTTPS
- **Render**: Managed container hosting
- **DigitalOcean App Platform**: Scalable container deployment
- **AWS ECS/Fargate**: Enterprise-grade container orchestration

### Option B: Self-Hosted with Docker Compose

```bash
# Copy production environment template
cp .env.production .env

# Edit .env with your actual values
nano .env

# Deploy with production compose file
docker-compose -f docker-compose.prod.yml up -d

# Check deployment status
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs hermes
```

## 4. SSL/TLS Configuration

### Option A: Let's Encrypt with Certbot
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificates
sudo certbot --nginx -d your-domain.com -d api.your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Option B: CloudFlare SSL Proxy
1. Add your domain to CloudFlare
2. Set SSL mode to "Full (Strict)"
3. Enable "Always Use HTTPS"
4. Configure origin certificates

## 5. Performance Optimization

### Database Optimization
```sql
-- Add database performance indexes
CREATE INDEX CONCURRENTLY idx_voice_sessions_user_created
ON voice_sessions(user_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_conversations_tenant_timestamp
ON conversations(tenant_id, created_at DESC);

-- Enable connection pooling
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
```

### Application Scaling
```yaml
# docker-compose.prod.yml scaling
services:
  hermes:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    environment:
      - WORKERS=4
      - WORKER_CLASS=gevent
      - MAX_REQUESTS=5000
```

### Redis Configuration
```bash
# External Redis setup (recommended)
# Use managed Redis from:
# - Supabase (if available)
# - Redis Cloud
# - AWS ElastiCache
# - DigitalOcean Managed Redis

export REDIS_URL="rediss://username:password@your-redis-host:6380"
```

## 6. Monitoring and Observability

### Health Monitoring
```bash
# Set up health check endpoints
curl https://your-domain.com/health
curl https://your-domain.com/status

# Monitor container health
docker-compose -f docker-compose.prod.yml exec hermes /usr/local/bin/healthcheck.sh
```

### Prometheus Metrics
```bash
# Start monitoring stack
docker-compose -f docker-compose.prod.yml --profile monitoring up -d

# Access Prometheus at http://your-domain:9090
# Configure alerts for:
# - Application uptime
# - Response time > 500ms
# - Memory usage > 80%
# - Database connection errors
```

### Log Aggregation
```bash
# Start logging stack
docker-compose -f docker-compose.prod.yml --profile logging up -d

# Access Kibana at http://your-domain:5601
# Set up log parsing for:
# - Voice session tracking
# - Error analysis
# - Performance metrics
# - Security events
```

## 7. Security Hardening

### Container Security
```dockerfile
# Security measures already implemented:
# - Non-root user execution
# - Minimal base image (Python slim)
# - No-new-privileges flag
# - Capability dropping
# - Read-only root filesystem where possible
# - Secrets management via environment variables
```

### Network Security
```yaml
# Nginx security headers (already configured)
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
```

### Database Security
```sql
-- Row Level Security (RLS) for multi-tenancy
ALTER TABLE voice_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY voice_sessions_tenant_policy ON voice_sessions
  FOR ALL TO authenticated
  USING (tenant_id = auth.jwt() ->> 'tenant_id');
```

## 8. Backup and Disaster Recovery

### Database Backups
```bash
# Automated Supabase backups are included
# For additional backups:
pg_dump $DATABASE_URL > hermes_backup_$(date +%Y%m%d_%H%M%S).sql

# Schedule with cron:
0 2 * * * pg_dump $DATABASE_URL | gzip > /backups/hermes_$(date +\%Y\%m\%d).sql.gz
```

### Application State Backup
```bash
# Backup persistent volumes
docker run --rm \
  -v hermes_data:/source:ro \
  -v /backup/location:/backup \
  alpine tar czf /backup/hermes_data_$(date +%Y%m%d).tar.gz -C /source .
```

## 9. Compliance and Legal Requirements

### GDPR Compliance
- **Data Retention**: Configured for 90 days (configurable)
- **Right to Erasure**: Implemented via API endpoints
- **Data Portability**: Export functionality available
- **Privacy by Design**: Minimal data collection

### HIPAA Compliance (if handling health data)
- **Encryption**: TLS 1.3 in transit, AES-256 at rest
- **Access Logs**: Comprehensive audit logging
- **User Authentication**: Multi-factor authentication ready
- **Data Backup**: Encrypted backup storage

### Legal Practice Requirements
- **Attorney-Client Privilege**: Secure communication channels
- **Document Retention**: Configurable retention policies
- **Audit Trail**: Complete interaction logging
- **Disclaimers**: Automatic legal disclaimers

## 10. Troubleshooting

### Common Issues

**Container Won't Start**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs hermes

# Check environment variables
docker-compose -f docker-compose.prod.yml exec hermes env | grep -E "(DATABASE|REDIS|OPENAI)"

# Test database connectivity
docker-compose -f docker-compose.prod.yml exec hermes python -c "
import asyncpg, asyncio, os
asyncio.run(asyncpg.connect(os.environ['DATABASE_URL']).fetchval('SELECT 1'))
print('Database connected successfully')
"
```

**High Memory Usage**
```bash
# Monitor memory usage
docker stats hermes-app-prod

# Adjust worker settings
# In .env file:
WORKERS=2
WORKER_CONNECTIONS=500
MAX_REQUESTS=2000
```

**WebSocket Connection Issues**
```bash
# Check nginx WebSocket proxy settings
docker-compose -f docker-compose.prod.yml exec nginx-prod nginx -t

# Test WebSocket connection
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: test" \
  https://your-domain.com/ws/voice
```

## 11. Support and Maintenance

### Regular Maintenance Tasks
```bash
# Weekly health check
./docker/healthcheck.sh

# Monthly log rotation
docker-compose -f docker-compose.prod.yml exec hermes logrotate -f /etc/logrotate.conf

# Quarterly security updates
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Performance Monitoring
- Monitor response times < 200ms
- Maintain uptime > 99.9%
- Database connection pool health
- Memory usage trends
- Voice processing latency

## 12. Scaling Considerations

### Horizontal Scaling
```yaml
# Load balancer configuration
services:
  hermes:
    deploy:
      replicas: 5

  nginx-prod:
    volumes:
      - ./nginx/load-balancer.conf:/etc/nginx/conf.d/default.conf
```

### Database Scaling
- **Read Replicas**: For analytics and reporting
- **Connection Pooling**: PgBouncer for connection management
- **Query Optimization**: Regular EXPLAIN ANALYZE on slow queries

This deployment guide provides a comprehensive foundation for running HERMES in production environments suitable for enterprise law firms with strict security and compliance requirements.