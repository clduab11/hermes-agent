---
name: "[MILESTONE 1] Docker Containerization Infrastructure"
about: Implement complete Docker containerization for production deployment
title: "[MILESTONE 1] Docker Containerization Infrastructure"
labels: infrastructure, deployment, critical, copilot-ready
assignees: ''
---

## 🎯 Objective

Implement complete Docker containerization infrastructure to enable production deployment of HERMES. This is a **CRITICAL BLOCKER** for production deployment per CLAUDE.md requirements.

**Current Status:** 0% - No Docker files exist
**Target Status:** 100% - Full Docker infrastructure with dev and prod configurations
**Completion Criteria:** All Docker files created, tested, and documented

---

## 📋 Prerequisites

- Docker Desktop installed and running
- Access to container registry (GCR, Docker Hub, or AWS ECR)
- Existing environment variables documented in `.env.example`
- PostgreSQL and Redis connection requirements understood

---

## ✅ Acceptance Criteria

- [ ] Production Dockerfile builds successfully
- [ ] Development Dockerfile builds successfully
- [ ] docker-compose.yml starts all services successfully
- [ ] docker-compose.prod.yml configured for production
- [ ] Voice pipeline works through Docker containers
- [ ] All integration tests pass in Docker environment
- [ ] Database migrations run successfully in Docker
- [ ] Documentation updated with Docker setup instructions
- [ ] CI/CD pipeline updated to build and push Docker images

---

## 📝 Step-by-Step Implementation Guide

### PHASE 1: Create Production Dockerfile

**File:** `Dockerfile`

```dockerfile
# Multi-stage build for production optimization
FROM python:3.11-slim as builder

# Install system dependencies for voice processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 hermes && \
    mkdir -p /app && \
    chown -R hermes:hermes /app

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 hermes && \
    mkdir -p /app && \
    chown -R hermes:hermes /app

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=hermes:hermes . .

# Switch to non-root user
USER hermes

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run with Uvicorn (production ASGI server)
CMD ["uvicorn", "hermes.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Tasks:**
- [ ] Create `Dockerfile` with the above content
- [ ] Verify all system dependencies are included
- [ ] Test build: `docker build -t hermes:latest .`
- [ ] Test run: `docker run -p 8000:8000 hermes:latest`
- [ ] Verify health check endpoint works

---

### PHASE 2: Create Development Dockerfile

**File:** `Dockerfile.dev`

```dockerfile
FROM python:3.11-slim

# Install system dependencies + development tools
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    curl \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies including dev tools
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    pytest-mock \
    black \
    isort \
    flake8 \
    mypy \
    ipdb \
    watchfiles

# Copy application code (will be overridden by volume mount)
COPY . .

# Expose port
EXPOSE 8000

# Development server with auto-reload
CMD ["uvicorn", "hermes.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Tasks:**
- [ ] Create `Dockerfile.dev` with the above content
- [ ] Include all development dependencies
- [ ] Test build: `docker build -f Dockerfile.dev -t hermes:dev .`
- [ ] Verify hot-reload functionality works

---

### PHASE 3: Create Development Docker Compose

**File:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:16-alpine
    container_name: hermes-postgres
    environment:
      POSTGRES_DB: hermes_dev
      POSTGRES_USER: hermes
      POSTGRES_PASSWORD: dev_password_change_in_production
      POSTGRES_INITDB_ARGS: "-E UTF8"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hermes -d hermes_dev"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - hermes-network

  # Redis Cache & Message Broker
  redis:
    image: redis:7-alpine
    container_name: hermes-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - hermes-network

  # HERMES API Service
  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: hermes-api
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      # Database
      DATABASE_URL: postgresql+asyncpg://hermes:dev_password_change_in_production@postgres:5432/hermes_dev

      # Redis
      REDIS_URL: redis://redis:6379/0

      # Application
      ENV: development
      DEBUG: "true"
      LOG_LEVEL: DEBUG

      # API Keys (load from .env file)
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
      CLIO_CLIENT_ID: ${CLIO_CLIENT_ID}
      CLIO_CLIENT_SECRET: ${CLIO_CLIENT_SECRET}
      LAWPAY_API_KEY: ${LAWPAY_API_KEY}
      STRIPE_API_KEY: ${STRIPE_API_KEY}

      # TTS Configuration
      KOKORO_TTS_MODE: api
      KOKORO_TTS_API_URL: http://kokoro-tts:8001

      # Security
      JWT_SECRET_KEY: dev_jwt_secret_change_in_production
      JWT_ALGORITHM: RS256

    ports:
      - "8000:8000"
    volumes:
      # Mount source code for hot-reload
      - .:/app
      # Persist logs
      - ./logs:/app/logs
    networks:
      - hermes-network
    command: uvicorn hermes.main:app --host 0.0.0.0 --port 8000 --reload

  # Celery Worker for Async Tasks
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: hermes-celery
    depends_on:
      - api
      - redis
      - postgres
    environment:
      DATABASE_URL: postgresql+asyncpg://hermes:dev_password_change_in_production@postgres:5432/hermes_dev
      REDIS_URL: redis://redis:6379/0
      ENV: development
    volumes:
      - .:/app
    networks:
      - hermes-network
    command: celery -A hermes.celery_app worker --loglevel=info

  # Kokoro TTS Service (Optional - if running locally)
  kokoro-tts:
    image: hexgrad/kokoro-fastapi:latest
    container_name: hermes-tts
    ports:
      - "8001:8001"
    environment:
      MODEL_PATH: /models
    volumes:
      - kokoro_models:/models
    networks:
      - hermes-network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  kokoro_models:
    driver: local

networks:
  hermes-network:
    driver: bridge
```

**Tasks:**
- [ ] Create `docker-compose.yml` with the above content
- [ ] Create `.env` file from `.env.example` with required API keys
- [ ] Create `scripts/init-db.sql` for database initialization
- [ ] Test: `docker-compose up -d`
- [ ] Verify all services start: `docker-compose ps`
- [ ] Test API health: `curl http://localhost:8000/health`
- [ ] Test database connection from API container
- [ ] Test Redis connection from API container
- [ ] Run migrations: `docker-compose exec api alembic upgrade head`

---

### PHASE 4: Create Production Docker Compose

**File:** `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: hermes-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./static:/usr/share/nginx/html/static:ro
    depends_on:
      - api
    networks:
      - hermes-network
    restart: always

  # HERMES API Service (Production)
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: hermes-api
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    env_file:
      - .env.production
    environment:
      ENV: production
      DEBUG: "false"
      LOG_LEVEL: INFO
    expose:
      - "8000"
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    networks:
      - hermes-network
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  # PostgreSQL (managed service recommended for production)
  postgres:
    image: postgres:16-alpine
    container_name: hermes-postgres
    env_file:
      - .env.production
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
    networks:
      - hermes-network
    restart: always
    deploy:
      resources:
        limits:
          memory: 2G

  # Redis (managed service recommended for production)
  redis:
    image: redis:7-alpine
    container_name: hermes-redis
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_prod_data:/data
    networks:
      - hermes-network
    restart: always
    deploy:
      resources:
        limits:
          memory: 1G

  # Celery Worker
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: hermes-celery
    depends_on:
      - api
    env_file:
      - .env.production
    command: celery -A hermes.celery_app worker --loglevel=info --concurrency=4
    networks:
      - hermes-network
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  # Prometheus Metrics (Optional)
  prometheus:
    image: prom/prometheus:latest
    container_name: hermes-prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"
    networks:
      - hermes-network
    restart: always

volumes:
  postgres_prod_data:
    driver: local
  redis_prod_data:
    driver: local
  prometheus_data:
    driver: local

networks:
  hermes-network:
    driver: bridge
```

**Tasks:**
- [ ] Create `docker-compose.prod.yml` with the above content
- [ ] Create `.env.production` with production secrets (DO NOT COMMIT)
- [ ] Add `.env.production` to `.gitignore`
- [ ] Create nginx configuration in `nginx/nginx.conf`
- [ ] Configure SSL certificates
- [ ] Set resource limits appropriately
- [ ] Test production build locally

---

### PHASE 5: Create Docker Ignore File

**File:** `.dockerignore`

```
# Git
.git
.gitignore
.github

# Python
__pycache__
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/
*.egg

# Virtual environments
.venv
venv/
ENV/
env/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.mypy_cache/

# Documentation
docs/
*.md
!README.md

# Environment files
.env
.env.*
!.env.example

# Logs
logs/
*.log

# Frontend
node_modules/
frontend/node_modules/

# Temporary files
tmp/
temp/
*.tmp

# Database
*.db
*.sqlite

# OS files
.DS_Store
Thumbs.db
```

**Tasks:**
- [ ] Create `.dockerignore` file
- [ ] Test that excluded files don't appear in Docker build context
- [ ] Verify build is faster with properly configured ignore

---

### PHASE 6: Create Nginx Configuration

**File:** `nginx/nginx.conf`

```nginx
events {
    worker_connections 1024;
}

http {
    upstream hermes_api {
        server api:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=ws_limit:10m rate=5r/s;

    server {
        listen 80;
        server_name _;

        # Redirect HTTP to HTTPS
        return 301 https://$host$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name _;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security Headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Max upload size
        client_max_body_size 50M;

        # API endpoints
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;

            proxy_pass http://hermes_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # WebSocket for voice pipeline
        location /ws/ {
            limit_req zone=ws_limit burst=10 nodelay;

            proxy_pass http://hermes_api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket timeouts
            proxy_connect_timeout 7d;
            proxy_send_timeout 7d;
            proxy_read_timeout 7d;
        }

        # Health check endpoint
        location /health {
            proxy_pass http://hermes_api/health;
            access_log off;
        }

        # Static files
        location /static/ {
            alias /usr/share/nginx/html/static/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

**Tasks:**
- [ ] Create `nginx/` directory
- [ ] Create `nginx/nginx.conf` with the above content
- [ ] Create self-signed SSL certificates for testing
- [ ] Test nginx configuration: `docker run --rm -v $(pwd)/nginx:/etc/nginx nginx nginx -t`

---

### PHASE 7: Create Database Initialization Script

**File:** `scripts/init-db.sql`

```sql
-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas for multi-tenancy
CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS audit;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE hermes_dev TO hermes;
GRANT ALL PRIVILEGES ON SCHEMA public TO hermes;
GRANT ALL PRIVILEGES ON SCHEMA audit TO hermes;

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit.activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    user_id UUID,
    action VARCHAR(255) NOT NULL,
    resource VARCHAR(255) NOT NULL,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for audit log
CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit.activity_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit.activity_log(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit.activity_log(action);

-- Enable Row Level Security
ALTER TABLE audit.activity_log ENABLE ROW LEVEL SECURITY;
```

**Tasks:**
- [ ] Create `scripts/` directory
- [ ] Create `scripts/init-db.sql`
- [ ] Test SQL script runs without errors
- [ ] Verify extensions are created

---

### PHASE 8: Update Documentation

**File:** `docs/docker-deployment.md`

Create comprehensive Docker deployment documentation including:
- Prerequisites and system requirements
- Local development setup with Docker
- Production deployment guide
- Environment variable reference
- Troubleshooting common issues
- Backup and recovery procedures
- Scaling strategies

**Tasks:**
- [ ] Create `docs/docker-deployment.md`
- [ ] Document all Docker commands
- [ ] Add troubleshooting section
- [ ] Include production deployment checklist
- [ ] Add diagrams of Docker architecture

**File:** `README.md` (Update)

Add Docker quick start section:

```markdown
## 🐳 Quick Start with Docker

### Development

1. Clone the repository:
   ```bash
   git clone https://github.com/clduab11/hermes-agent.git
   cd hermes-agent
   ```

2. Copy environment file:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Start services:
   ```bash
   docker-compose up -d
   ```

4. Run migrations:
   ```bash
   docker-compose exec api alembic upgrade head
   ```

5. Access the API:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

### Production

See [Docker Deployment Guide](docs/docker-deployment.md) for production setup.
```

**Tasks:**
- [ ] Update README.md with Docker section
- [ ] Add badges for Docker build status
- [ ] Link to detailed deployment docs

---

### PHASE 9: Configure CI/CD for Docker

**File:** `.github/workflows/docker-build.yml`

```yaml
name: Docker Build & Push

on:
  push:
    branches: [main, develop]
    tags:
      - 'v*'
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
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
        if: github.event_name != 'pull_request'
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

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Run Trivy security scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'

  test-docker:
    runs-on: ubuntu-latest
    needs: build-and-push

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Create .env file
        run: |
          cp .env.example .env
          echo "OPENROUTER_API_KEY=${{ secrets.OPENROUTER_API_KEY }}" >> .env

      - name: Start services
        run: docker-compose up -d

      - name: Wait for services
        run: |
          timeout 60 bash -c 'until docker-compose exec -T api curl -f http://localhost:8000/health; do sleep 2; done'

      - name: Run migrations
        run: docker-compose exec -T api alembic upgrade head

      - name: Run tests in Docker
        run: docker-compose exec -T api pytest tests/ -v

      - name: Stop services
        if: always()
        run: docker-compose down -v
```

**Tasks:**
- [ ] Create `.github/workflows/docker-build.yml`
- [ ] Configure GitHub Container Registry
- [ ] Add required secrets to GitHub repository
- [ ] Test workflow triggers correctly
- [ ] Verify images are pushed to registry

---

### PHASE 10: Testing & Validation

**Tasks:**

- [ ] **Local Build Test**
  ```bash
  docker build -t hermes:test .
  docker run -p 8000:8000 hermes:test
  curl http://localhost:8000/health
  ```

- [ ] **Compose Test**
  ```bash
  docker-compose up -d
  docker-compose ps  # All services should be healthy
  docker-compose logs api  # Check for errors
  ```

- [ ] **Migration Test**
  ```bash
  docker-compose exec api alembic upgrade head
  docker-compose exec api alembic current
  ```

- [ ] **Voice Pipeline Test**
  - Start Docker services
  - Test WebSocket connection to voice endpoint
  - Send test audio data
  - Verify STT → LLM → TTS pipeline works
  - Check latency is acceptable

- [ ] **Integration Test**
  ```bash
  docker-compose exec api pytest tests/integration/ -v
  ```

- [ ] **Load Test**
  - Use locust or similar tool
  - Test 50+ concurrent connections
  - Monitor container resource usage
  - Verify no crashes or memory leaks

- [ ] **Production Build Test**
  ```bash
  docker-compose -f docker-compose.prod.yml up -d
  # Test all production configurations
  ```

- [ ] **Security Scan**
  ```bash
  docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image hermes:latest
  ```

---

## 📊 Validation Checklist

Before marking this issue as complete, ensure:

- [ ] All Docker files created and committed to repository
- [ ] Development environment starts successfully with `docker-compose up`
- [ ] Production environment configured (even if not deployed yet)
- [ ] All services communicate correctly (API ↔ Postgres ↔ Redis)
- [ ] Database migrations work in Docker
- [ ] Voice pipeline functional through containers
- [ ] Integration tests pass in Docker environment
- [ ] Documentation complete and accurate
- [ ] CI/CD pipeline builds and pushes images
- [ ] Security scanning integrated
- [ ] No hardcoded secrets in Docker files
- [ ] Resource limits configured for production
- [ ] Health checks working for all services
- [ ] Logs are accessible and properly formatted

---

## 🔗 Related Files

Files that will be created/modified:
```
├── Dockerfile                          # Production image
├── Dockerfile.dev                      # Development image
├── docker-compose.yml                  # Development orchestration
├── docker-compose.prod.yml             # Production orchestration
├── .dockerignore                       # Build context exclusions
├── nginx/
│   └── nginx.conf                      # Reverse proxy config
├── scripts/
│   └── init-db.sql                     # Database initialization
├── .github/workflows/
│   └── docker-build.yml                # CI/CD for Docker
├── docs/
│   └── docker-deployment.md            # Deployment guide
└── README.md                           # Updated with Docker instructions
```

---

## 🎯 Success Metrics

- Docker build time: < 5 minutes
- Container startup time: < 30 seconds
- Memory usage (API container): < 2GB under normal load
- All services reach healthy state within 60 seconds
- Zero security vulnerabilities in Docker image (Trivy scan)

---

## 💡 AI Coding Assistant Instructions

This issue is optimized for autonomous implementation by AI coding assistants (GitHub Copilot, Cursor, etc.).

**Recommended approach:**
1. Execute phases sequentially (1 → 10)
2. Create each file exactly as specified in the templates
3. Test each phase before moving to the next
4. Check off each task in the checklist as completed
5. Run validation commands after each phase
6. Create a PR when all phases are complete

**Important notes:**
- All file paths are absolute from repository root
- All code blocks are production-ready templates
- Environment variables should use `.env` file pattern
- Never commit secrets or `.env.production` file
- Test thoroughly before marking complete

---

## 📚 Reference Documentation

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI in Containers](https://fastapi.tiangolo.com/deployment/docker/)
- [Multi-stage Docker Builds](https://docs.docker.com/build/building/multi-stage/)
- HERMES CLAUDE.md guidelines (repository root)

---

**Issue Priority:** 🔴 **CRITICAL**
**Estimated Complexity:** Medium-High
**Blocking:** Production Deployment
**Dependencies:** None
**Milestone:** Production Readiness - Phase 1
