#!/bin/bash
set -euo pipefail

# ===== HERMES Docker Clean Script =====
# Clean up Docker resources (containers, images, volumes)
# Usage: ./scripts/docker-clean.sh [--all] [--volumes] [--images]

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
CLEAN_CONTAINERS=false
CLEAN_IMAGES=false
CLEAN_VOLUMES=false
CLEAN_ALL=false

# Parse arguments
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}No options specified. Use --help to see available options.${NC}"
    echo "Cleaning stopped containers only (safe operation)..."
    CLEAN_CONTAINERS=true
fi

for arg in "$@"; do
    case $arg in
        --all)
            CLEAN_ALL=true
            CLEAN_CONTAINERS=true
            CLEAN_IMAGES=true
            CLEAN_VOLUMES=true
            shift
            ;;
        --volumes|-v)
            CLEAN_VOLUMES=true
            shift
            ;;
        --images|-i)
            CLEAN_IMAGES=true
            shift
            ;;
        --containers|-c)
            CLEAN_CONTAINERS=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--all] [--volumes] [--images] [--containers]"
            echo ""
            echo "Options:"
            echo "  --all         Clean everything (⚠️  destructive!)"
            echo "  --containers  Remove stopped containers"
            echo "  --images      Remove HERMES Docker images"
            echo "  --volumes     Remove Docker volumes (⚠️  deletes data!)"
            echo "  --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Remove stopped containers only"
            echo "  $0 --images           # Remove HERMES images"
            echo "  $0 --all              # Remove everything"
            echo ""
            echo "⚠️  WARNING: --volumes and --all will DELETE ALL DATA!"
            exit 0
            ;;
    esac
done

echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   HERMES Docker Cleanup Script                ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════╝${NC}"
echo ""

# Warn about destructive operations
if [ "$CLEAN_VOLUMES" = true ] || [ "$CLEAN_ALL" = true ]; then
    echo -e "${RED}⚠️  WARNING: This will DELETE ALL DATA in Docker volumes!${NC}"
    echo "This includes:"
    echo "  - PostgreSQL database data"
    echo "  - Redis cache data"
    echo "  - Application logs"
    echo ""
    read -p "Are you ABSOLUTELY sure? Type 'DELETE' to confirm: " -r
    echo
    if [[ ! $REPLY =~ ^DELETE$ ]]; then
        echo "Cancelled."
        exit 1
    fi
fi

# Stop all services first
echo -e "${YELLOW}Stopping all services...${NC}"
docker-compose -f docker-compose.yml down 2>/dev/null || true
docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
echo -e "${GREEN}✓ Services stopped${NC}"
echo ""

# Clean containers
if [ "$CLEAN_CONTAINERS" = true ]; then
    echo -e "${YELLOW}Removing stopped containers...${NC}"
    # Remove HERMES-specific containers
    docker container prune -f --filter "label=com.hermes.service" || true
    echo -e "${GREEN}✓ Containers removed${NC}"
    echo ""
fi

# Clean images
if [ "$CLEAN_IMAGES" = true ]; then
    echo -e "${YELLOW}Removing HERMES Docker images...${NC}"
    docker images hermes-api --format "{{.ID}}" | xargs -r docker rmi -f || true
    docker image prune -f --filter "label=com.hermes.version" || true
    echo -e "${GREEN}✓ Images removed${NC}"
    echo ""
fi

# Clean volumes
if [ "$CLEAN_VOLUMES" = true ]; then
    echo -e "${RED}Removing Docker volumes (DATA WILL BE DELETED)...${NC}"
    docker-compose -f docker-compose.yml down --volumes 2>/dev/null || true
    docker-compose -f docker-compose.dev.yml down --volumes 2>/dev/null || true
    docker volume prune -f || true
    echo -e "${GREEN}✓ Volumes removed${NC}"
    echo ""
fi

# Show summary
echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Cleanup Complete!                           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════╝${NC}"
echo ""

# Show remaining Docker resources
echo "Remaining Docker resources:"
echo ""
echo -e "${YELLOW}Images:${NC}"
docker images hermes-api 2>/dev/null || echo "  None"
echo ""
echo -e "${YELLOW}Volumes:${NC}"
docker volume ls --filter "name=hermes" 2>/dev/null || echo "  None"
echo ""
echo -e "${YELLOW}Containers:${NC}"
docker ps -a --filter "name=hermes" 2>/dev/null || echo "  None"

echo ""
echo "Next steps:"
echo "  Rebuild:  ./scripts/docker-build.sh"
echo "  Start:    ./scripts/docker-start.sh"
