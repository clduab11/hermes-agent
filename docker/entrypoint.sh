#!/bin/bash
# HERMES AI Voice Agent System - Production Entrypoint Script
# Handles graceful startup, environment validation, and process management

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_debug() {
    if [[ "${DEBUG}" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
    fi
}

# Trap signals for graceful shutdown
cleanup() {
    log_info "Received shutdown signal, cleaning up..."
    if [[ -n "$GUNICORN_PID" ]]; then
        log_info "Stopping Gunicorn process (PID: $GUNICORN_PID)..."
        kill -TERM "$GUNICORN_PID" 2>/dev/null || true
        wait "$GUNICORN_PID" 2>/dev/null || true
    fi
    log_info "Cleanup completed"
    exit 0
}

trap cleanup SIGTERM SIGINT SIGQUIT

# Environment validation
validate_environment() {
    log_info "Validating environment configuration..."

    local missing_vars=()

    # Production-only requirements
    if [[ "${DEBUG}" != "true" && "${DEMO_MODE}" != "true" ]]; then
        if [[ -z "${OPENAI_API_KEY}" ]]; then
            missing_vars+=("OPENAI_API_KEY")
        fi

        if [[ -z "${JWT_PRIVATE_KEY}" || -z "${JWT_PUBLIC_KEY}" ]]; then
            missing_vars+=("JWT_PRIVATE_KEY" "JWT_PUBLIC_KEY")
        fi

        if [[ -z "${DATABASE_URL}" ]]; then
            missing_vars+=("DATABASE_URL")
        fi
    fi

    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        exit 1
    fi

    log_info "Environment validation completed successfully"
}

# Database readiness check
wait_for_database() {
    if [[ -z "${DATABASE_URL}" ]]; then
        log_warn "No DATABASE_URL provided, skipping database connectivity check"
        return 0
    fi

    log_info "Waiting for database to become ready..."

    local max_attempts=30
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if python -c "
import asyncpg
import asyncio
import sys
import os

async def test_connection():
    try:
        conn = await asyncpg.connect(os.environ['DATABASE_URL'])
        await conn.fetchval('SELECT 1')
        await conn.close()
        return True
    except Exception as e:
        print(f'Database not ready: {e}', file=sys.stderr)
        return False

if asyncio.run(test_connection()):
    sys.exit(0)
else:
    sys.exit(1)
"; then
            log_info "Database is ready"
            break
        fi

        log_debug "Database not ready (attempt $attempt/$max_attempts), waiting 2 seconds..."
        sleep 2
        ((attempt++))
    done

    if [[ $attempt -gt $max_attempts ]]; then
        log_error "Database failed to become ready within timeout period"
        exit 1
    fi
}

# Redis readiness check
wait_for_redis() {
    if [[ -z "${REDIS_URL}" ]]; then
        log_warn "No REDIS_URL provided, skipping Redis connectivity check"
        return 0
    fi

    log_info "Waiting for Redis to become ready..."

    local max_attempts=30
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if python -c "
import redis
import sys
import os
from urllib.parse import urlparse

try:
    redis_url = os.environ['REDIS_URL']
    parsed_url = urlparse(redis_url)
    r = redis.Redis(
        host=parsed_url.hostname or 'localhost',
        port=parsed_url.port or 6379,
        db=0,
        socket_timeout=5
    )
    r.ping()
    print('Redis is ready')
    sys.exit(0)
except Exception as e:
    print(f'Redis not ready: {e}', file=sys.stderr)
    sys.exit(1)
"; then
            log_info "Redis is ready"
            break
        fi

        log_debug "Redis not ready (attempt $attempt/$max_attempts), waiting 2 seconds..."
        sleep 2
        ((attempt++))
    done

    if [[ $attempt -gt $max_attempts ]]; then
        log_error "Redis failed to become ready within timeout period"
        exit 1
    fi
}

# Database migrations
run_migrations() {
    if [[ -z "${DATABASE_URL}" ]]; then
        log_warn "No DATABASE_URL provided, skipping database migrations"
        return 0
    fi

    log_info "Running database migrations..."

    if command -v alembic >/dev/null 2>&1; then
        if alembic upgrade head; then
            log_info "Database migrations completed successfully"
        else
            log_error "Database migrations failed"
            exit 1
        fi
    else
        log_warn "Alembic not found, skipping database migrations"
    fi
}

# Pre-flight checks
preflight_checks() {
    log_info "Running pre-flight checks..."

    # Check Python environment
    log_debug "Python version: $(python --version)"
    log_debug "Python path: $(which python)"

    # Check critical Python packages
    python -c "
import importlib
import sys

critical_packages = [
    'fastapi',
    'uvicorn',
    'pydantic',
    'sqlalchemy',
    'redis',
    'openai',
    'gunicorn'
]

missing = []
for package in critical_packages:
    try:
        importlib.import_module(package)
    except ImportError:
        missing.append(package)

if missing:
    print(f'Missing critical packages: {missing}', file=sys.stderr)
    sys.exit(1)
else:
    print('All critical packages are available')
"

    # Check file permissions
    if [[ ! -r "/app/hermes/main.py" ]]; then
        log_error "Cannot read main application file"
        exit 1
    fi

    # Check log directory
    if [[ ! -d "/app/logs" ]]; then
        log_warn "Log directory does not exist, creating..."
        mkdir -p /app/logs
    fi

    # Check tmp directory
    if [[ ! -d "/app/tmp" ]]; then
        log_warn "Temp directory does not exist, creating..."
        mkdir -p /app/tmp
    fi

    log_info "Pre-flight checks completed successfully"
}

# Start the application
start_application() {
    log_info "Starting HERMES AI Voice Agent System..."

    # Set defaults for production
    export WORKERS=${WORKERS:-4}
    export WORKER_CLASS=${WORKER_CLASS:-gevent}
    export WORKER_CONNECTIONS=${WORKER_CONNECTIONS:-1000}
    export MAX_REQUESTS=${MAX_REQUESTS:-1000}
    export MAX_REQUESTS_JITTER=${MAX_REQUESTS_JITTER:-100}
    export TIMEOUT=${TIMEOUT:-30}
    export KEEPALIVE=${KEEPALIVE:-2}
    export BIND_ADDRESS=${API_HOST:-0.0.0.0}:${API_PORT:-8000}

    # Choose startup mode
    if [[ "${DEBUG}" == "true" ]]; then
        log_info "Starting in development mode with auto-reload..."
        exec python -m uvicorn hermes.main:app \
            --host "${API_HOST:-0.0.0.0}" \
            --port "${API_PORT:-8000}" \
            --reload \
            --log-level debug
    else
        log_info "Starting in production mode with Gunicorn..."
        log_info "Workers: $WORKERS, Worker Class: $WORKER_CLASS"
        log_info "Bind Address: $BIND_ADDRESS"

        # Start Gunicorn in background to allow signal handling
        gunicorn hermes.main:app \
            --bind "$BIND_ADDRESS" \
            --workers "$WORKERS" \
            --worker-class "$WORKER_CLASS" \
            --worker-connections "$WORKER_CONNECTIONS" \
            --max-requests "$MAX_REQUESTS" \
            --max-requests-jitter "$MAX_REQUESTS_JITTER" \
            --timeout "$TIMEOUT" \
            --keepalive "$KEEPALIVE" \
            --preload \
            --enable-stdio-inheritance \
            --log-level info \
            --access-logfile - \
            --error-logfile - \
            --capture-output &

        GUNICORN_PID=$!
        log_info "Gunicorn started with PID: $GUNICORN_PID"

        # Wait for the process
        wait $GUNICORN_PID
    fi
}

# Main execution
main() {
    log_info "HERMES AI Voice Agent System - Production Container Starting"
    log_info "Build Environment: ${BUILD_ENV:-production}"
    log_info "Debug Mode: ${DEBUG:-false}"
    log_info "Demo Mode: ${DEMO_MODE:-false}"

    # Run all startup procedures
    validate_environment
    wait_for_database
    wait_for_redis
    run_migrations
    preflight_checks
    start_application
}

# Execute main function
main "$@"