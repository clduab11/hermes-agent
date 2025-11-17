#!/bin/bash
# ===== HERMES Production Deployment Script =====
# Automated deployment to production environment
# Usage: ./scripts/deploy-production.sh
#
# Prerequisites:
# - Git repository with v1.0.0 tag
# - Docker and Docker Compose installed
# - SSL certificates configured
# - Environment variables set in .env.production
# - Database backups configured
#
# Safety: This script includes multiple confirmation prompts

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}🚀 HERMES Production Deployment Script${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Function to print colored status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to confirm critical actions
confirm_action() {
    local message="$1"
    echo -e "${YELLOW}⚠ WARNING:${NC} $message"
    read -p "Type 'DEPLOY' to confirm: " confirmation
    if [ "$confirmation" != "DEPLOY" ]; then
        print_error "Deployment cancelled by user"
        exit 1
    fi
}

# Step 1: Pre-deployment checks
echo -e "${BLUE}Step 1: Pre-deployment Checks${NC}"
echo "================================"

# Check if we're in the project root
if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Are you in the project root?"
    exit 1
fi
print_status "Project root verified"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi
print_status "Docker is running"

# Check if .env.production exists
if [ ! -f "$PROJECT_ROOT/.env.production" ]; then
    print_error ".env.production not found. Please create it from .env.example"
    exit 1
fi
print_status ".env.production found"

# Check if SSL certificates exist
if [ ! -d "$PROJECT_ROOT/nginx/ssl" ] && [ ! -d "/etc/letsencrypt/live" ]; then
    print_warning "SSL certificates not found. HTTPS will not work!"
    read -p "Continue anyway? (yes/no): " continue_without_ssl
    if [ "$continue_without_ssl" != "yes" ]; then
        exit 1
    fi
else
    print_status "SSL certificates configured"
fi

# Check git status
if [ -n "$(git status --porcelain)" ]; then
    print_warning "Working directory is not clean. Uncommitted changes detected."
    git status --short
    read -p "Continue anyway? (yes/no): " continue_dirty
    if [ "$continue_dirty" != "yes" ]; then
        exit 1
    fi
else
    print_status "Working directory clean"
fi

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
print_status "Current branch: $CURRENT_BRANCH"

# Check if v1.0.0 tag exists
if ! git tag | grep -q "^v1.0.0$"; then
    print_warning "Git tag v1.0.0 not found"
    read -p "Create tag v1.0.0 now? (yes/no): " create_tag
    if [ "$create_tag" == "yes" ]; then
        git tag -a v1.0.0 -m "HERMES Production Release v1.0.0 - 100% Ready 🚀"
        print_status "Created tag v1.0.0"
    fi
else
    print_status "Git tag v1.0.0 exists"
fi

echo ""

# Step 2: Backup current state
echo -e "${BLUE}Step 2: Backup Current State${NC}"
echo "================================"

# Create backup directory
BACKUP_DIR="$PROJECT_ROOT/backups/pre-deploy-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
print_status "Created backup directory: $BACKUP_DIR"

# Backup environment file
if [ -f "$PROJECT_ROOT/.env.production" ]; then
    cp "$PROJECT_ROOT/.env.production" "$BACKUP_DIR/.env.production.backup"
    print_status "Backed up .env.production"
fi

# Backup database (if running)
if docker-compose ps | grep -q "postgres.*Up"; then
    print_status "Backing up database..."
    docker-compose exec -T postgres pg_dump -U postgres hermes_production > "$BACKUP_DIR/database_backup.sql"
    print_status "Database backed up to $BACKUP_DIR/database_backup.sql"
else
    print_warning "PostgreSQL not running, skipping database backup"
fi

echo ""

# Step 3: Stop current services
echo -e "${BLUE}Step 3: Stop Current Services${NC}"
echo "================================"

confirm_action "This will stop all running HERMES services. All active connections will be dropped."

print_status "Stopping services gracefully..."
docker-compose down --timeout 30

print_status "All services stopped"
echo ""

# Step 4: Pull latest images and rebuild
echo -e "${BLUE}Step 4: Build Production Images${NC}"
echo "================================"

print_status "Building production Docker images..."
docker-compose -f docker-compose.yml build --no-cache

print_status "Production images built successfully"
echo ""

# Step 5: Database migrations
echo -e "${BLUE}Step 5: Database Migrations${NC}"
echo "================================"

print_status "Starting database for migrations..."
docker-compose up -d postgres redis

# Wait for database to be ready
print_status "Waiting for database to be ready..."
sleep 10

print_status "Running database migrations..."
docker-compose run --rm api alembic upgrade head

print_status "Database migrations completed"
echo ""

# Step 6: Start production services
echo -e "${BLUE}Step 6: Start Production Services${NC}"
echo "================================"

confirm_action "This will start HERMES in production mode with all services."

print_status "Starting all services..."
docker-compose up -d

# Wait for services to be healthy
print_status "Waiting for services to be healthy (30 seconds)..."
sleep 30

echo ""

# Step 7: Health checks
echo -e "${BLUE}Step 7: Health Checks${NC}"
echo "================================"

# Check if services are running
print_status "Checking service status..."
docker-compose ps

# Check API health endpoint
print_status "Checking API health endpoint..."
for i in {1..5}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_status "API health check: OK"
        break
    else
        if [ $i -eq 5 ]; then
            print_error "API health check failed after 5 attempts"
            print_warning "Check logs with: docker-compose logs api"
            exit 1
        fi
        print_warning "Attempt $i failed, retrying in 5 seconds..."
        sleep 5
    fi
done

# Check database connection
print_status "Checking database connection..."
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    print_status "Database connection: OK"
else
    print_error "Database connection failed"
    exit 1
fi

# Check Redis connection
print_status "Checking Redis connection..."
if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    print_status "Redis connection: OK"
else
    print_error "Redis connection failed"
    exit 1
fi

echo ""

# Step 8: Smoke tests
echo -e "${BLUE}Step 8: Smoke Tests${NC}"
echo "================================"

print_status "Running smoke tests..."

# Test 1: API root endpoint
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    print_status "API root endpoint: OK"
else
    print_warning "API root endpoint: FAILED (non-critical)"
fi

# Test 2: OpenAPI docs
if curl -f http://localhost:8000/docs > /dev/null 2>&1; then
    print_status "API documentation: OK"
else
    print_warning "API documentation: FAILED (non-critical)"
fi

# Test 3: Check logs for errors
print_status "Checking logs for errors..."
ERROR_COUNT=$(docker-compose logs api | grep -i "error" | wc -l)
if [ "$ERROR_COUNT" -gt 0 ]; then
    print_warning "Found $ERROR_COUNT error lines in logs (review recommended)"
else
    print_status "No errors in logs"
fi

echo ""

# Step 9: Deployment summary
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✅ DEPLOYMENT SUCCESSFUL!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "Deployment Summary:"
echo "-------------------"
echo "• Backup location: $BACKUP_DIR"
echo "• Git tag: v1.0.0"
echo "• Services running: $(docker-compose ps | grep "Up" | wc -l)"
echo "• API health: ✓"
echo "• Database health: ✓"
echo "• Redis health: ✓"
echo ""
echo "Next Steps:"
echo "-----------"
echo "1. Monitor logs for 30 minutes:"
echo "   docker-compose logs -f api"
echo ""
echo "2. Test all critical endpoints:"
echo "   curl -f https://your-domain.com/health"
echo "   curl -f https://your-domain.com/api/v1/auth/health"
echo ""
echo "3. Review monitoring dashboards (if configured)"
echo ""
echo "4. Notify stakeholders of successful deployment"
echo ""
echo "5. Begin 24-hour monitoring period (see LAUNCH_CHECKLIST.md)"
echo ""
echo "Rollback Command (if needed):"
echo "-----------------------------"
echo "docker-compose down && docker-compose up -d"
echo "# Then restore database: cat $BACKUP_DIR/database_backup.sql | docker-compose exec -T postgres psql -U postgres hermes_production"
echo ""
echo -e "${GREEN}🎉 HERMES is live in production!${NC}"
echo -e "${BLUE}============================================${NC}"
