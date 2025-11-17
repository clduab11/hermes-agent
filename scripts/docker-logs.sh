#!/bin/bash
set -euo pipefail

# ===== HERMES Docker Logs Script =====
# View logs from HERMES services
# Usage: ./scripts/docker-logs.sh [service] [--follow] [--tail N]

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
SERVICE=""
FOLLOW_FLAG=""
TAIL_FLAG=""
COMPOSE_FILE="docker-compose.yml"

# Detect which environment is running
if docker-compose -f docker-compose.dev.yml ps -q > /dev/null 2>&1; then
    COMPOSE_FILE="docker-compose.dev.yml"
    ENVIRONMENT="development"
else
    COMPOSE_FILE="docker-compose.yml"
    ENVIRONMENT="production"
fi

# Parse arguments
for arg in "$@"; do
    case $arg in
        api|postgres|redis|nginx)
            SERVICE="$arg"
            shift
            ;;
        --follow|-f)
            FOLLOW_FLAG="--follow"
            shift
            ;;
        --tail)
            TAIL_FLAG="--tail ${2:-100}"
            shift 2
            ;;
        --dev)
            COMPOSE_FILE="docker-compose.dev.yml"
            ENVIRONMENT="development"
            shift
            ;;
        --prod)
            COMPOSE_FILE="docker-compose.yml"
            ENVIRONMENT="production"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [service] [--follow] [--tail N]"
            echo ""
            echo "Services:"
            echo "  api           API service logs"
            echo "  postgres      PostgreSQL logs"
            echo "  redis         Redis logs"
            echo "  nginx         Nginx logs (production only)"
            echo "  (none)        All services logs"
            echo ""
            echo "Options:"
            echo "  --follow      Follow log output"
            echo "  --tail N      Show last N lines (default: 100)"
            echo "  --dev         Force development environment"
            echo "  --prod        Force production environment"
            echo "  --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Show all logs"
            echo "  $0 api --follow       # Follow API logs"
            echo "  $0 postgres --tail 50 # Last 50 lines of postgres logs"
            exit 0
            ;;
    esac
done

echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   HERMES Docker Logs                          ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════╝${NC}"
echo ""
echo "Environment: $ENVIRONMENT"
echo "Service: ${SERVICE:-all}"
echo ""

# Check if services are running
if ! docker-compose -f "$COMPOSE_FILE" ps -q > /dev/null 2>&1; then
    echo -e "${RED}✗ No services are running${NC}"
    echo "Start services with: ./scripts/docker-start.sh"
    exit 1
fi

# Show logs
docker-compose -f "$COMPOSE_FILE" logs ${FOLLOW_FLAG} ${TAIL_FLAG} ${SERVICE} || {
    echo -e "${RED}✗ Failed to get logs${NC}"
    exit 1
}
