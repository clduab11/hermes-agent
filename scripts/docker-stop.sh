#!/bin/bash
set -euo pipefail

# ===== HERMES Docker Stop Script =====
# Gracefully stops HERMES services
# Usage: ./scripts/docker-stop.sh [production|dev] [--remove]

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default environment
ENVIRONMENT=${1:-production}
REMOVE_FLAG=""
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
        --remove|-v)
            REMOVE_FLAG="--volumes"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [production|dev] [--remove]"
            echo ""
            echo "Arguments:"
            echo "  production    Stop production environment (default)"
            echo "  dev           Stop development environment"
            echo ""
            echo "Options:"
            echo "  --remove      Remove volumes (⚠️  deletes data!)"
            echo "  --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 dev               # Stop development environment"
            echo "  $0 production        # Stop production environment"
            echo "  $0 dev --remove      # Stop dev and remove volumes"
            exit 0
            ;;
    esac
done

echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   HERMES Docker Stop Script                   ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════╝${NC}"
echo ""

if [ -n "$REMOVE_FLAG" ]; then
    echo -e "${RED}⚠️  WARNING: This will remove volumes and DELETE ALL DATA!${NC}"
    read -p "Are you sure? Type 'yes' to confirm: " -r
    echo
    if [[ ! $REPLY =~ ^yes$ ]]; then
        echo "Cancelled."
        exit 1
    fi
fi

echo -e "${GREEN}Stopping HERMES ($ENVIRONMENT mode)...${NC}"
echo "  Compose file: $COMPOSE_FILE"
echo "  Remove volumes: ${REMOVE_FLAG:+yes}"
echo ""

# Stop services
docker-compose -f "$COMPOSE_FILE" down ${REMOVE_FLAG} || {
    echo -e "${RED}✗ Failed to stop services${NC}"
    exit 1
}

echo ""
echo -e "${GREEN}✓ Services stopped successfully${NC}"

if [ -n "$REMOVE_FLAG" ]; then
    echo -e "${YELLOW}  All volumes removed${NC}"
fi

echo ""
echo "Next steps:"
echo "  Start again:  ./scripts/docker-start.sh $ENVIRONMENT"
echo "  View images:  docker images hermes-api"
echo "  Clean all:    ./scripts/docker-clean.sh"
