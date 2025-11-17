# ===== HERMES AI Voice Agent - Production Dockerfile =====
# Multi-stage build for optimized production image
# Target size: <500MB
# Security: Non-root user, minimal attack surface
# ===== Stage 1: Builder =====
FROM python:3.11-slim as builder

LABEL maintainer="Parallax Analytics"
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

# Copy only requirements first (layer caching optimization)
COPY requirements.txt requirements-ci.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip wheel setuptools && \
    pip install --no-cache-dir -r requirements.txt

# ===== Stage 2: Runtime =====
FROM python:3.11-slim

# OCI image labels for metadata
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.title="HERMES AI Voice Agent"
LABEL org.opencontainers.image.description="24/7 AI-powered voice agent for law firms"
LABEL org.opencontainers.image.vendor="Parallax Analytics"
LABEL org.opencontainers.image.licenses="Proprietary"
LABEL org.opencontainers.image.url="https://github.com/clduab11/hermes-agent"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ffmpeg \
    libsndfile1 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r hermes && \
    useradd -r -g hermes -u 1000 -m -s /sbin/nologin hermes && \
    mkdir -p /app /app/logs /app/data && \
    chown -R hermes:hermes /app

# Copy virtual environment from builder
COPY --from=builder --chown=hermes:hermes /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code with proper ownership
COPY --chown=hermes:hermes hermes/ ./hermes/
COPY --chown=hermes:hermes alembic/ ./alembic/
COPY --chown=hermes:hermes alembic.ini pyproject.toml ./
COPY --chown=hermes:hermes scripts/*.py ./scripts/

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH" \
    PORT=8000 \
    WORKERS=4

# Switch to non-root user
USER hermes

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["sh", "-c", "uvicorn hermes.main:app --host 0.0.0.0 --port ${PORT} --workers ${WORKERS}"]
