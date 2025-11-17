# [PRODUCTION] Comprehensive Docker Containerization Infrastructure

**Status**: 🔴 Critical - Production Blocker
**Priority**: P0 - Immediate
**Estimated Effort**: 32 hours
**Target Completion**: 81% → 95%
**Dependencies**: None

---

## Executive Summary

Implement production-grade Docker containerization for HERMES AI Voice Agent System to enable:
- ✅ Consistent deployment across environments
- ✅ Horizontal scaling with orchestration
- ✅ Zero-downtime deployments
- ✅ Environment isolation and security
- ✅ CI/CD pipeline integration

---

## Phase 1: Production Dockerfile (4 hours)

### 1.1 Multi-Stage Python Dockerfile
**File**: `Dockerfile`

```dockerfile
# ===== Stage 1: Builder =====
FROM python:3.11-slim as builder

LABEL maintainer="Parallax Analytics <contact@example.com>"
LABEL description="HERMES AI Voice Agent - Production Build Stage"

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=1.0.0

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only requirements first (layer caching)
COPY requirements.txt requirements-ci.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip wheel setuptools && \
    pip install --no-cache-dir -r requirements.txt

# ===== Stage 2: Runtime =====
FROM python:3.11-slim

LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.title="HERMES AI Voice Agent"
LABEL org.opencontainers.image.description="24/7 AI-powered voice agent for law firms"
LABEL org.opencontainers.image.vendor="Parallax Analytics"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ffmpeg \
    libsndfile1 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r hermes && useradd -r -g hermes -u 1000 hermes && \
    mkdir -p /app /app/logs /app/data && \
    chown -R hermes:hermes /app

# Copy virtual environment from builder
COPY --from=builder --chown=hermes:hermes /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=hermes:hermes hermes/ ./hermes/
COPY --chown=hermes:hermes alembic/ ./alembic/
COPY --chown=hermes:hermes alembic.ini pyproject.toml ./
COPY --chown=hermes:hermes scripts/ ./scripts/

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH" \
    PORT=8000

# Switch to non-root user
USER hermes

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE 8000

# Default command (override in docker-compose)
CMD ["uvicorn", "hermes.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Tasks**:
- [ ] Create multi-stage Dockerfile with builder pattern
- [ ] Implement layer caching optimization
- [ ] Add non-root user for security
- [ ] Configure health checks
- [ ] Add OCI image labels
- [ ] Optimize image size (<500MB target)

---

## Phase 2: Development Dockerfile (2 hours)

### 2.1 Dockerfile.dev
**File**: `Dockerfile.dev`

```dockerfile
FROM python:3.11-slim

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    ffmpeg \
    libsndfile1 \
    git \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt requirements-ci.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -r requirements-ci.txt && \
    pip install --no-cache-dir \
    pytest-watch \
    ipython \
    ipdb

# Copy application code
COPY . .

# Development mode - run with hot reload
ENV PYTHONUNBUFFERED=1 \
    DEVELOPMENT_MODE=true

EXPOSE 8000

CMD ["uvicorn", "hermes.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Tasks**:
- [ ] Create development Dockerfile with hot reload
- [ ] Include development tools (pytest-watch, ipdb)
- [ ] Mount source code as volume
- [ ] Configure for rapid iteration

---

## Phase 3: Docker Compose Orchestration (6 hours)

### 3.1 Production Docker Compose
**File**: `docker-compose.yml`

```yaml
version: '3.9'

services:
  # ===== HERMES API Service =====
  api:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        BUILD_DATE: ${BUILD_DATE:-2025-01-01}
        VCS_REF: ${VCS_REF:-dev}
        VERSION: ${VERSION:-1.0.0}
    image: hermes-api:${VERSION:-latest}
    container_name: hermes-api
    restart: unless-stopped
    ports:
      - "${API_PORT:-8000}:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=production
      - LOG_LEVEL=${LOG_LEVEL:-info}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - CLIO_CLIENT_ID=${CLIO_CLIENT_ID}
      - CLIO_CLIENT_SECRET=${CLIO_CLIENT_SECRET}
      - STRIPE_API_KEY=${STRIPE_API_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    env_file:
      - .env.production
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - hermes-network
    labels:
      - "com.hermes.service=api"
      - "com.hermes.version=${VERSION:-1.0.0}"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # ===== PostgreSQL Database =====
  postgres:
    image: postgres:16-alpine
    container_name: hermes-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=${POSTGRES_USER:-postgres}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB:-hermes}
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --lc-collate=C --lc-ctype=C
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./db/sql:/docker-entrypoint-initdb.d:ro
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    networks:
      - hermes-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ===== Redis Cache =====
  redis:
    image: redis:7-alpine
    container_name: hermes-redis
    restart: unless-stopped
    command: >
      redis-server
      --appendonly yes
      --appendfilename "appendonly.aof"
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
      --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    ports:
      - "${REDIS_PORT:-6379}:6379"
    networks:
      - hermes-network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # ===== Nginx Reverse Proxy =====
  nginx:
    image: nginx:alpine
    container_name: hermes-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./static:/usr/share/nginx/html/static:ro
    depends_on:
      - api
    networks:
      - hermes-network
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ===== Prometheus Monitoring =====
  prometheus:
    image: prom/prometheus:latest
    container_name: hermes-prometheus
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    ports:
      - "${PROMETHEUS_PORT:-9090}:9090"
    networks:
      - hermes-network

  # ===== Grafana Dashboard =====
  grafana:
    image: grafana/grafana:latest
    container_name: hermes-grafana
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_INSTALL_PLUGINS=grafana-clock-panel
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro
    ports:
      - "${GRAFANA_PORT:-3000}:3000"
    depends_on:
      - prometheus
    networks:
      - hermes-network

volumes:
  postgres-data:
    driver: local
  redis-data:
    driver: local
  prometheus-data:
    driver: local
  grafana-data:
    driver: local

networks:
  hermes-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16
```

**Tasks**:
- [ ] Create production docker-compose.yml
- [ ] Configure all services with health checks
- [ ] Implement volume management
- [ ] Set up service dependencies
- [ ] Configure networking
- [ ] Add monitoring stack (Prometheus + Grafana)

---

### 3.2 Development Docker Compose
**File**: `docker-compose.dev.yml`

```yaml
version: '3.9'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    image: hermes-api:dev
    container_name: hermes-api-dev
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/hermes_dev
      - REDIS_URL=redis://redis:6379/0
      - DEVELOPMENT_MODE=true
      - LOG_LEVEL=debug
    env_file:
      - .env.example
    volumes:
      - .:/app:delegated
      - /app/hermes/__pycache__
    depends_on:
      - postgres
      - redis
    networks:
      - hermes-dev-network
    command: uvicorn hermes.main:app --host 0.0.0.0 --port 8000 --reload

  postgres:
    image: postgres:16-alpine
    container_name: hermes-postgres-dev
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=hermes_dev
    volumes:
      - postgres-dev-data:/var/lib/postgresql/data
    ports:
      - "5433:5432"
    networks:
      - hermes-dev-network

  redis:
    image: redis:7-alpine
    container_name: hermes-redis-dev
    ports:
      - "6380:6379"
    networks:
      - hermes-dev-network

  # ===== Testing Database =====
  postgres-test:
    image: postgres:16-alpine
    container_name: hermes-postgres-test
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=hermes_test
    tmpfs:
      - /var/lib/postgresql/data
    ports:
      - "5434:5432"
    networks:
      - hermes-dev-network

volumes:
  postgres-dev-data:

networks:
  hermes-dev-network:
    driver: bridge
```

**Tasks**:
- [ ] Create development docker-compose
- [ ] Configure hot reload for development
- [ ] Add testing database
- [ ] Mount source code as volumes
- [ ] Simplify for rapid iteration

---

## Phase 4: Nginx Reverse Proxy (4 hours)

### 4.1 Nginx Configuration
**File**: `nginx/nginx.conf`

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 2048;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss
               application/rss+xml font/truetype font/opentype
               application/vnd.ms-fontobject image/svg+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
    limit_req_zone $binary_remote_addr zone=voice_limit:10m rate=50r/s;
    limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Include virtual host configs
    include /etc/nginx/conf.d/*.conf;
}
```

**File**: `nginx/conf.d/hermes.conf`

```nginx
upstream hermes_api {
    least_conn;
    server api:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

# HTTP redirect to HTTPS
server {
    listen 80;
    server_name _;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name hermes.example.com;

    # SSL configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Static files
    location /static/ {
        alias /usr/share/nginx/html/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API endpoints
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        limit_conn conn_limit 10;

        proxy_pass http://hermes_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
    }

    # WebSocket for voice pipeline
    location /ws/ {
        limit_req zone=voice_limit burst=10 nodelay;

        proxy_pass http://hermes_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
        proxy_buffering off;
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://hermes_api/health;
    }
}
```

**Tasks**:
- [ ] Create Nginx configuration with SSL
- [ ] Configure WebSocket support for voice pipeline
- [ ] Implement rate limiting
- [ ] Add security headers
- [ ] Configure gzip compression
- [ ] Set up upstream load balancing

---

## Phase 5: .dockerignore Optimization (1 hour)

**File**: `.dockerignore`

```
# Version control
.git
.gitignore
.github

# Python
__pycache__
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
.pytest_cache/
.coverage
htmlcov/
.tox/
.hypothesis/

# Environment
.env
.env.*
!.env.example
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Documentation
*.md
!README.md
docs/
.roo/
.claude/

# Testing
tests/
*.test.js
*.spec.js

# Logs
*.log
logs/

# Frontend
frontend/node_modules/
frontend/dist/
frontend/build/

# Deployment
deployment/
monitoring/prometheus-data/
monitoring/grafana-data/

# Data
data/
*.db
*.sqlite

# Media
*.mp3
*.wav
*.ogg
```

**Tasks**:
- [ ] Create comprehensive .dockerignore
- [ ] Reduce build context size
- [ ] Exclude development files
- [ ] Optimize layer caching

---

## Phase 6: Docker Scripts & Automation (3 hours)

### 6.1 Build Script
**File**: `scripts/docker-build.sh`

```bash
#!/bin/bash
set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building HERMES Docker Images...${NC}"

# Get version from git
VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "dev")
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Build production image
echo -e "${YELLOW}Building production image...${NC}"
docker build \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg VCS_REF="${VCS_REF}" \
    --build-arg VERSION="${VERSION}" \
    --tag "hermes-api:${VERSION}" \
    --tag "hermes-api:latest" \
    --file Dockerfile \
    .

# Build development image
echo -e "${YELLOW}Building development image...${NC}"
docker build \
    --tag "hermes-api:dev" \
    --file Dockerfile.dev \
    .

echo -e "${GREEN}✓ Build complete!${NC}"
echo "Production image: hermes-api:${VERSION}"
echo "Development image: hermes-api:dev"
```

### 6.2 Start Script
**File**: `scripts/docker-start.sh`

```bash
#!/bin/bash
set -euo pipefail

ENVIRONMENT=${1:-production}

if [ "$ENVIRONMENT" = "dev" ]; then
    echo "Starting development environment..."
    docker-compose -f docker-compose.dev.yml up -d
else
    echo "Starting production environment..."
    docker-compose up -d
fi

echo "Waiting for services to be healthy..."
sleep 10

docker-compose ps

echo ""
echo "HERMES is running!"
echo "API: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo "Grafana: http://localhost:3000"
```

**Tasks**:
- [ ] Create automated build script
- [ ] Create start/stop scripts
- [ ] Add version tagging
- [ ] Implement health checks

---

## Phase 7: CI/CD Integration (4 hours)

### 7.1 GitHub Actions Docker Workflow
**File**: `.github/workflows/docker-build.yml`

```yaml
name: Docker Build and Push

on:
  push:
    branches: [main, develop]
    tags: ['v*']
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            BUILD_DATE=${{ github.event.head_commit.timestamp }}
            VCS_REF=${{ github.sha }}
            VERSION=${{ steps.meta.outputs.version }}
```

**Tasks**:
- [ ] Create GitHub Actions workflow
- [ ] Configure Docker registry
- [ ] Implement multi-arch builds
- [ ] Add image scanning
- [ ] Configure caching

---

## Phase 8: Environment Configuration (2 hours)

### 8.1 Docker Environment Files
**File**: `.env.docker.example`

```bash
# ===== Docker Environment Configuration =====

# Application
VERSION=1.0.0
ENVIRONMENT=production
LOG_LEVEL=info

# API Service
API_PORT=8000
API_WORKERS=4

# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=CHANGE_ME_SECURE_PASSWORD
POSTGRES_DB=hermes
POSTGRES_PORT=5432

# Redis
REDIS_PASSWORD=CHANGE_ME_REDIS_PASSWORD
REDIS_PORT=6379

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_PASSWORD=CHANGE_ME_GRAFANA_PASSWORD

# OpenAI
OPENAI_API_KEY=sk-...

# Clio Integration
CLIO_CLIENT_ID=...
CLIO_CLIENT_SECRET=...

# Stripe Billing
STRIPE_API_KEY=sk_...

# Security
JWT_SECRET_KEY=CHANGE_ME_64_CHAR_SECRET
SECRET_KEY=CHANGE_ME_32_CHAR_SECRET
```

**Tasks**:
- [ ] Create Docker-specific env template
- [ ] Document all variables
- [ ] Add validation script
- [ ] Secure secrets management

---

## Phase 9: Monitoring & Logging (4 hours)

### 9.1 Prometheus Configuration
**File**: `monitoring/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'hermes-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
```

**Tasks**:
- [ ] Configure Prometheus scraping
- [ ] Set up Grafana dashboards
- [ ] Configure alerting rules
- [ ] Add log aggregation

---

## Phase 10: Documentation & Testing (2 hours)

### 10.1 Docker Documentation
**File**: `docs/DOCKER.md`

```markdown
# HERMES Docker Deployment Guide

## Quick Start

### Production
\`\`\`bash
# Build images
./scripts/docker-build.sh

# Start services
./scripts/docker-start.sh production

# Check status
docker-compose ps
\`\`\`

### Development
\`\`\`bash
# Start development environment
./scripts/docker-start.sh dev

# View logs
docker-compose -f docker-compose.dev.yml logs -f api
\`\`\`

## Architecture

[Diagram of Docker services]

## Scaling

\`\`\`bash
# Scale API service
docker-compose up -d --scale api=3
\`\`\`

## Troubleshooting

### Common Issues
1. **Port already in use**
   - Change port in .env file
2. **Database connection failed**
   - Check POSTGRES_PASSWORD is set
3. **Out of memory**
   - Increase Docker memory limit
\`\`\`

**Tasks**:
- [ ] Write comprehensive Docker documentation
- [ ] Create troubleshooting guide
- [ ] Add architecture diagrams
- [ ] Test all scenarios
- [ ] Verify 80%+ coverage integration

---

## Acceptance Criteria

### Production Readiness
- [ ] Multi-stage Dockerfile with <500MB image size
- [ ] Docker Compose with all services orchestrated
- [ ] Nginx reverse proxy with SSL termination
- [ ] Health checks for all services
- [ ] Non-root user security
- [ ] Volume persistence configured
- [ ] Network isolation implemented
- [ ] Monitoring stack operational
- [ ] CI/CD pipeline integrated
- [ ] Documentation complete

### Performance Metrics
- [ ] Container startup time <30s
- [ ] Image build time <5 minutes
- [ ] Memory usage <2GB per container
- [ ] CPU usage <50% under load
- [ ] Zero-downtime deployments verified

### Security Checklist
- [ ] No secrets in images
- [ ] Non-root containers
- [ ] Network segmentation
- [ ] SSL/TLS encryption
- [ ] Image vulnerability scanning
- [ ] Security headers configured

---

## Progress Tracking

| Phase | Tasks | Status | Hours |
|-------|-------|--------|-------|
| 1. Production Dockerfile | 6 | ⬜ | 4 |
| 2. Development Dockerfile | 4 | ⬜ | 2 |
| 3. Docker Compose | 6 | ⬜ | 6 |
| 4. Nginx Configuration | 6 | ⬜ | 4 |
| 5. .dockerignore | 4 | ⬜ | 1 |
| 6. Scripts & Automation | 4 | ⬜ | 3 |
| 7. CI/CD Integration | 5 | ⬜ | 4 |
| 8. Environment Config | 4 | ⬜ | 2 |
| 9. Monitoring & Logging | 4 | ⬜ | 4 |
| 10. Documentation & Testing | 4 | ⬜ | 2 |
| **TOTAL** | **47 tasks** | **0%** | **32h** |

---

## Timeline

- **Week 1**: Phases 1-5 (Core Docker infrastructure)
- **Week 2**: Phases 6-10 (Automation, monitoring, documentation)

**Target**: 81% → 95% production readiness

---

*Issue Template v1.0 - Created for PR #65 - HERMES Production Deployment*
