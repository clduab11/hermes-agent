#!/bin/bash
# HERMES AI Voice Agent System - Health Check Script
# Comprehensive health monitoring for production deployments

set -e

# Configuration
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-http://localhost:8000/health}"
STATUS_ENDPOINT="${STATUS_ENDPOINT:-http://localhost:8000/status}"
TIMEOUT="${HEALTH_TIMEOUT:-10}"
MAX_RETRIES="${HEALTH_MAX_RETRIES:-3}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[HEALTH]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[HEALTH]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[HEALTH]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

# Check if the main process is running
check_process() {
    local python_processes
    python_processes=$(pgrep -f "python.*hermes" || true)

    if [[ -z "$python_processes" ]]; then
        log_error "No HERMES Python processes found"
        return 1
    fi

    log_info "HERMES processes running: $(echo $python_processes | wc -w)"
    return 0
}

# Check basic HTTP health endpoint
check_http_health() {
    local attempt=1

    while [[ $attempt -le $MAX_RETRIES ]]; do
        if curl -sf --max-time "$TIMEOUT" "$HEALTH_ENDPOINT" >/dev/null 2>&1; then
            log_info "HTTP health check passed (attempt $attempt)"
            return 0
        fi

        log_warn "HTTP health check failed (attempt $attempt/$MAX_RETRIES)"
        ((attempt++))

        if [[ $attempt -le $MAX_RETRIES ]]; then
            sleep 2
        fi
    done

    log_error "HTTP health check failed after $MAX_RETRIES attempts"
    return 1
}

# Check detailed application status
check_application_status() {
    local response
    local status
    local components_healthy=0
    local components_total=0

    # Get status with timeout
    if ! response=$(curl -sf --max-time "$TIMEOUT" "$STATUS_ENDPOINT" 2>/dev/null); then
        log_error "Failed to retrieve application status"
        return 1
    fi

    # Parse JSON response (basic parsing without jq)
    status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")

    if [[ "$status" != "operational" ]]; then
        log_error "Application status is not operational: $status"
        return 1
    fi

    # Check critical components
    local critical_components=("voice_pipeline" "websocket_handler" "mcp_orchestrator")

    for component in "${critical_components[@]}"; do
        ((components_total++))
        if echo "$response" | grep -q "\"$component\":\"\\(initialized\\|active\\|ready\\)\""; then
            ((components_healthy++))
            log_info "Component $component is healthy"
        else
            log_warn "Component $component is not healthy"
        fi
    done

    local health_ratio
    health_ratio=$(echo "scale=2; $components_healthy / $components_total" | bc -l 2>/dev/null || echo "0")

    if (( $(echo "$health_ratio < 0.8" | bc -l 2>/dev/null || echo "1") )); then
        log_error "Component health ratio too low: $health_ratio ($components_healthy/$components_total)"
        return 1
    fi

    log_info "Application status check passed ($components_healthy/$components_total components healthy)"
    return 0
}

# Check database connectivity
check_database() {
    if [[ -z "$DATABASE_URL" ]]; then
        log_info "DATABASE_URL not set, skipping database check"
        return 0
    fi

    if python3 -c "
import asyncpg
import asyncio
import sys
import os

async def test_db():
    try:
        conn = await asyncpg.connect(os.environ['DATABASE_URL'])
        result = await conn.fetchval('SELECT 1')
        await conn.close()
        return result == 1
    except Exception as e:
        print(f'Database error: {e}', file=sys.stderr)
        return False

if asyncio.run(test_db()):
    sys.exit(0)
else:
    sys.exit(1)
" 2>/dev/null; then
        log_info "Database connectivity check passed"
        return 0
    else
        log_error "Database connectivity check failed"
        return 1
    fi
}

# Check Redis connectivity
check_redis() {
    if [[ -z "$REDIS_URL" ]]; then
        log_info "REDIS_URL not set, skipping Redis check"
        return 0
    fi

    if python3 -c "
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
    sys.exit(0)
except Exception as e:
    print(f'Redis error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null; then
        log_info "Redis connectivity check passed"
        return 0
    else
        log_error "Redis connectivity check failed"
        return 1
    fi
}

# Check memory usage
check_memory_usage() {
    local memory_limit_mb=2048  # 2GB default limit
    local memory_warning_threshold=80  # 80% warning threshold

    # Get memory usage in MB
    local memory_usage_kb
    local memory_usage_mb
    local memory_percentage

    if command -v free >/dev/null 2>&1; then
        memory_usage_kb=$(free | awk '/^Mem:/{print $3}')
        memory_usage_mb=$((memory_usage_kb / 1024))
    elif [[ -f /proc/meminfo ]]; then
        local mem_total_kb
        local mem_available_kb
        mem_total_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        mem_available_kb=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
        memory_usage_mb=$(((mem_total_kb - mem_available_kb) / 1024))
    else
        log_warn "Cannot determine memory usage"
        return 0
    fi

    memory_percentage=$((memory_usage_mb * 100 / memory_limit_mb))

    if [[ $memory_percentage -gt 95 ]]; then
        log_error "Memory usage critical: ${memory_usage_mb}MB (${memory_percentage}%)"
        return 1
    elif [[ $memory_percentage -gt $memory_warning_threshold ]]; then
        log_warn "Memory usage high: ${memory_usage_mb}MB (${memory_percentage}%)"
    else
        log_info "Memory usage normal: ${memory_usage_mb}MB (${memory_percentage}%)"
    fi

    return 0
}

# Check disk space
check_disk_space() {
    local disk_warning_threshold=85  # 85% warning threshold
    local disk_critical_threshold=95  # 95% critical threshold

    local disk_usage
    disk_usage=$(df /app | tail -1 | awk '{print $5}' | sed 's/%//')

    if [[ $disk_usage -gt $disk_critical_threshold ]]; then
        log_error "Disk usage critical: ${disk_usage}%"
        return 1
    elif [[ $disk_usage -gt $disk_warning_threshold ]]; then
        log_warn "Disk usage high: ${disk_usage}%"
    else
        log_info "Disk usage normal: ${disk_usage}%"
    fi

    return 0
}

# Comprehensive health check
run_health_checks() {
    local checks_passed=0
    local checks_total=0
    local exit_code=0

    log_info "Starting comprehensive health checks..."

    # Core application checks
    ((checks_total++))
    if check_process; then
        ((checks_passed++))
    else
        exit_code=1
    fi

    ((checks_total++))
    if check_http_health; then
        ((checks_passed++))
    else
        exit_code=1
    fi

    ((checks_total++))
    if check_application_status; then
        ((checks_passed++))
    else
        exit_code=1
    fi

    # Infrastructure checks
    ((checks_total++))
    if check_database; then
        ((checks_passed++))
    fi

    ((checks_total++))
    if check_redis; then
        ((checks_passed++))
    fi

    # Resource checks
    ((checks_total++))
    if check_memory_usage; then
        ((checks_passed++))
    fi

    ((checks_total++))
    if check_disk_space; then
        ((checks_passed++))
    fi

    # Summary
    local success_rate
    success_rate=$(echo "scale=1; $checks_passed * 100 / $checks_total" | bc -l 2>/dev/null || echo "0")

    if [[ $exit_code -eq 0 ]]; then
        log_info "Health check PASSED: $checks_passed/$checks_total checks successful (${success_rate}%)"
    else
        log_error "Health check FAILED: $checks_passed/$checks_total checks successful (${success_rate}%)"
    fi

    return $exit_code
}

# Main execution
main() {
    # Install bc for calculations if not available
    if ! command -v bc >/dev/null 2>&1; then
        log_warn "bc calculator not available, some checks may be limited"
    fi

    run_health_checks
}

# Execute main function
main "$@"