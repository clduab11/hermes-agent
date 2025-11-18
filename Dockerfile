# HERMES Production Dockerfile
# Multi-stage build for optimized production image
#
# Required Environment Variables (set at runtime):
# - SUPABASE_DATABASE_URL
# - SUPABASE_PROJECT_URL
# - SUPABASE_SERVICE_KEY
# - OPENAI_API_KEY
# - JWT_PRIVATE_KEY
# - JWT_PUBLIC_KEY
# - STRIPE_API_KEY
# - STRIPE_WEBHOOK_SECRET
# - API_KEY_ENCRYPTION_SECRET
# See .env.example for full list

# Stage 1: Builder
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements and build wheels
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r hermesuser -g 1000 && \
    useradd -r -g hermesuser -u 1000 hermesuser

# Set working directory
WORKDIR /app

# Copy wheels from builder and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

# Copy application code
COPY hermes/ ./hermes/
COPY static/ ./static/
COPY templates/ ./templates/
COPY pyproject.toml ./

# Set ownership to non-root user
RUN chown -R hermesuser:hermesuser /app

# Switch to non-root user
USER hermesuser

# Expose port
EXPOSE 8000

# Health check using existing endpoints
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Run with uvicorn
CMD ["uvicorn", "hermes.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
