#!/bin/bash
set -euo pipefail

# ===== HERMES Docker Build Script =====
# Builds production and development Docker images
# Usage: ./scripts/docker-build.sh [--no-cache] [--prod-only] [--dev-only]

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
NO_CACHE=""
BUILD_PROD=true
BUILD_DEV=true

for arg in "$@"; do
    case $arg in
        --no-cache)
            NO_CACHE="--no-cache"
            shift
            ;;
        --prod-only)
            BUILD_DEV=false
            shift
            ;;
        --dev-only)
            BUILD_PROD=false
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--no-cache] [--prod-only] [--dev-only]"
            echo ""
            echo "Options:"
            echo "  --no-cache    Build without using cache"
            echo "  --prod-only   Build only production image"
            echo "  --dev-only    Build only development image"
            echo "  --help        Show this help message"
            exit 0
            ;;
    esac
done

echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   HERMES Docker Image Build Script           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════╝${NC}"
echo ""

# Get version information from git
VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "dev")
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo -e "${YELLOW}Build Information:${NC}"
echo "  Version:    $VERSION"
echo "  Build Date: $BUILD_DATE"
echo "  VCS Ref:    $VCS_REF"
echo ""

# Build production image
if [ "$BUILD_PROD" = true ]; then
    echo -e "${GREEN}━━━ Building Production Image ━━━${NC}"
    echo "  Image: hermes-api:${VERSION}"
    echo "  Tag:   hermes-api:latest"
    echo ""

    docker build \
        ${NO_CACHE} \
        --build-arg BUILD_DATE="${BUILD_DATE}" \
        --build-arg VCS_REF="${VCS_REF}" \
        --build-arg VERSION="${VERSION}" \
        --tag "hermes-api:${VERSION}" \
        --tag "hermes-api:latest" \
        --file Dockerfile \
        . || {
            echo -e "${RED}✗ Production build failed!${NC}"
            exit 1
        }

    # Get image size
    SIZE=$(docker images hermes-api:latest --format "{{.Size}}")
    echo ""
    echo -e "${GREEN}✓ Production image built successfully${NC}"
    echo "  Size: $SIZE"
fi

# Build development image
if [ "$BUILD_DEV" = true ]; then
    echo ""
    echo -e "${GREEN}━━━ Building Development Image ━━━${NC}"
    echo "  Image: hermes-api:dev"
    echo ""

    docker build \
        ${NO_CACHE} \
        --tag "hermes-api:dev" \
        --file Dockerfile.dev \
        . || {
            echo -e "${RED}✗ Development build failed!${NC}"
            exit 1
        }

    # Get image size
    SIZE=$(docker images hermes-api:dev --format "{{.Size}}")
    echo ""
    echo -e "${GREEN}✓ Development image built successfully${NC}"
    echo "  Size: $SIZE"
fi

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Build Complete!                             ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════╝${NC}"
echo ""

# Show built images
echo "Built images:"
docker images hermes-api --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | head -n 5

echo ""
echo "Next steps:"
echo "  - Start production:  ./scripts/docker-start.sh production"
echo "  - Start development: ./scripts/docker-start.sh dev"
echo "  - View help:         ./scripts/docker-start.sh --help"
