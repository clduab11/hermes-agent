#!/bin/bash
set -euo pipefail

# ===== HERMES Docker Start Script =====
# Starts HERMES services in production or development mode
# Usage: ./scripts/docker-start.sh [production|dev] [--build] [--detach]

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default environment
ENVIRONMENT=${1:-production}
BUILD_FLAG=""
DETACH_FLAG="-d"
COMPOSE_FILE="docker-compose.yml"

# Parse arguments
for arg in "$@"; do
    case $arg in
        production|prod)
            ENVIRONMENT="production"
            COMPOSE_FILE="docker-compose.yml"
            shift
            ;;
        development|dev)
            ENVIRONMENT="dev"
            COMPOSE_FILE="docker-compose.dev.yml"
            shift
            ;;
        --build)
            BUILD_FLAG="--build"
            shift
            ;;
        --no-detach|--attach)
            DETACH_FLAG=""
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [production|dev] [--build] [--no-detach]"
            echo ""
            echo "Arguments:"
            echo "  production    Start in production mode (default)"
            echo "  dev           Start in development mode with hot reload"
            echo ""
            echo "Options:"
            echo "  --build       Rebuild images before starting"
            echo "  --no-detach   Run in foreground (see logs in terminal)"
            echo "  --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 dev --build           # Build and start development environment"
            echo "  $0 production            # Start production environment"
            echo "  $0 dev --no-detach       # Start dev and show logs"
            exit 0
            ;;
    esac
done

echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   HERMES Docker Start Script                  ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════╝${NC}"
echo ""

# Check if .env file exists for production
if [ "$ENVIRONMENT" = "production" ]; then
    if [ ! -f ".env.production" ]; then
        echo -e "${YELLOW}⚠️  Warning: .env.production not found${NC}"
        echo "Creating from .env.docker.example..."
        cp .env.docker.example .env.production
        echo -e "${RED}✗ Please configure .env.production with your credentials${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}Starting HERMES in ${ENVIRONMENT} mode...${NC}"
echo "  Compose file: $COMPOSE_FILE"
echo "  Build: ${BUILD_FLAG:-no}"
echo "  Detached: ${DETACH_FLAG:+yes}"
echo ""

# Start services
docker-compose -f "$COMPOSE_FILE" up ${BUILD_FLAG} ${DETACH_FLAG} || {
    echo -e "${RED}✗ Failed to start services${NC}"
    exit 1
}

# If running in detached mode, show status
if [ -n "$DETACH_FLAG" ]; then
    echo ""
    echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
    sleep 5

    # Show service status
    echo ""
    docker-compose -f "$COMPOSE_FILE" ps

    # Check health status
    echo ""
    echo -e "${GREEN}━━━ Service Health Status ━━━${NC}"

    # Check API health
    echo -n "  API: "
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Healthy${NC}"
    else
        echo -e "${YELLOW}⚠ Starting... (check logs if this persists)${NC}"
    fi

    # Check PostgreSQL
    echo -n "  PostgreSQL: "
    if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ready${NC}"
    else
        echo -e "${YELLOW}⚠ Starting...${NC}"
    fi

    # Check Redis
    echo -n "  Redis: "
    if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ready${NC}"
    else
        echo -e "${YELLOW}⚠ Starting...${NC}"
    fi

    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   HERMES is running!                          ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Access points:"
    echo "  API:          http://localhost:8000"
    echo "  API Docs:     http://localhost:8000/docs"
    echo "  Health:       http://localhost:8000/health"
    echo "  PostgreSQL:   localhost:5432 (production) or 5433 (dev)"
    echo "  Redis:        localhost:6379 (production) or 6380 (dev)"
    echo ""
    echo "Useful commands:"
    echo "  View logs:    ./scripts/docker-logs.sh"
    echo "  Stop:         ./scripts/docker-stop.sh"
    echo "  Clean:        ./scripts/docker-clean.sh"
fi
