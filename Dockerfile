# HERMES AI Voice Agent System - Production Dockerfile
# Multi-stage build for optimal security, performance, and image size
# Optimized for enterprise law firm deployments on Supabase

#########################
# Build Stage
#########################
FROM python:3.11-slim as builder

# Build arguments
ARG BUILD_ENV=production
ARG PYTHON_VERSION=3.11

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install additional production dependencies
RUN pip install --no-cache-dir \
    gunicorn[gevent]==21.2.0 \
    gevent==23.9.1 \
    psycopg2-binary==2.9.9

# Copy application code
COPY hermes/ ./hermes/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY static/ ./static/

# Create non-root user for security
RUN groupadd -r hermes && useradd -r -g hermes hermes

# Set proper permissions
RUN chown -R hermes:hermes /app && \
    chown -R hermes:hermes /opt/venv

#########################
# Production Stage
#########################
FROM python:3.11-slim as production

# Build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=1.0.0

# Labels for container metadata
LABEL maintainer="HERMES Development Team" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="HERMES AI Voice Agent" \
      org.label-schema.description="Enterprise Reception & Matter Engagement System" \
      org.label-schema.version=$VERSION \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/your-org/hermes-agent" \
      org.label-schema.schema-version="1.0"

# Environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH" \
    DEBIAN_FRONTEND=noninteractive \
    # Production security settings
    WORKERS=4 \
    WORKER_CLASS=gevent \
    WORKER_CONNECTIONS=1000 \
    MAX_REQUESTS=1000 \
    MAX_REQUESTS_JITTER=100 \
    TIMEOUT=30 \
    KEEPALIVE=2 \
    # Application settings
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    DEBUG=false \
    DEMO_MODE=false

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Runtime libraries
    libpq5 \
    libssl3 \
    libffi8 \
    ca-certificates \
    # Audio processing libraries
    ffmpeg \
    libsndfile1 \
    # Health check utilities
    curl \
    # Security tools
    dumb-init \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get clean

# Create non-root user and group
RUN groupadd -r -g 1000 hermes && \
    useradd -r -u 1000 -g hermes -s /sbin/nologin \
    -c "HERMES Application User" hermes

# Copy virtual environment from builder
COPY --from=builder --chown=hermes:hermes /opt/venv /opt/venv

# Copy application from builder
COPY --from=builder --chown=hermes:hermes /app /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/tmp /app/data && \
    chown -R hermes:hermes /app/logs /app/tmp /app/data && \
    chmod 755 /app/logs /app/tmp /app/data

# Set working directory
WORKDIR /app

# Copy startup script
COPY --chown=hermes:hermes docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Copy health check script
COPY --chown=hermes:hermes docker/healthcheck.sh /usr/local/bin/healthcheck.sh
RUN chmod +x /usr/local/bin/healthcheck.sh

# Switch to non-root user
USER hermes

# Expose port
EXPOSE 8000

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# Security: Remove shell access and use dumb-init
ENTRYPOINT ["dumb-init", "--"]
CMD ["/usr/local/bin/entrypoint.sh"]

#########################
# Development Stage
#########################
FROM builder as development

# Development environment variables
ENV DEBUG=true \
    DEMO_MODE=true \
    API_HOST=0.0.0.0 \
    API_PORT=8000

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest==7.4.3 \
    pytest-asyncio==0.21.1 \
    pytest-cov==4.1.0 \
    black==23.11.0 \
    flake8==6.1.0 \
    mypy==1.7.1 \
    isort==5.12.0

# Switch to non-root user
USER hermes

# Expose port for development
EXPOSE 8000

# Development command with auto-reload
CMD ["python", "-m", "uvicorn", "hermes.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]