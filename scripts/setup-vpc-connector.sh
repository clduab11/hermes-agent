#!/bin/bash

# ====================================================================
# HERMES VPC Connector Setup Script
# ====================================================================
# Creates a VPC Access Connector for secure private communication
# between App Engine and Supabase/Redis or other private resources.
#
# Usage:
#   ./scripts/setup-vpc-connector.sh [OPTIONS]
#
# Options:
#   --project PROJECT_ID   GCP project ID (default: from gcloud config)
#   --region REGION        GCP region (default: us-central1)
#   --name NAME            Connector name (default: hermes-connector)
#   --ip-range CIDR        IP range (default: 10.8.0.0/28)
#   --dry-run              Show what would be done without making changes
#
# Cost: ~$30/month for connector + data processing fees
# ====================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Default values
PROJECT_ID=""
REGION="us-central1"
CONNECTOR_NAME="hermes-connector"
IP_RANGE="10.8.0.0/28"
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project) PROJECT_ID="$2"; shift 2 ;;
        --region) REGION="$2"; shift 2 ;;
        --name) CONNECTOR_NAME="$2"; shift 2 ;;
        --ip-range) IP_RANGE="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        *) log_error "Unknown option: $1"; exit 1 ;;
    esac
done

# Get project ID if not specified
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        log_error "No GCP project set. Use --project or set default project."
        exit 1
    fi
fi

echo "🌐 HERMES VPC Connector Setup"
echo ""
log_info "Configuration:"
echo "  Project:   $PROJECT_ID"
echo "  Region:    $REGION"
echo "  Name:      $CONNECTOR_NAME"
echo "  IP Range:  $IP_RANGE"
echo ""

# Check gcloud auth
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    log_error "Not authenticated with gcloud. Run: gcloud auth login"
    exit 1
fi

# Check if connector already exists
if gcloud compute networks vpc-access connectors describe "$CONNECTOR_NAME" \
    --region="$REGION" --project="$PROJECT_ID" &>/dev/null; then
    log_warning "VPC connector '$CONNECTOR_NAME' already exists"
    echo ""
    gcloud compute networks vpc-access connectors describe "$CONNECTOR_NAME" \
        --region="$REGION" --project="$PROJECT_ID"
    echo ""
    log_info "Connector is ready to use"
    exit 0
fi

if [ "$DRY_RUN" = true ]; then
    log_info "[DRY-RUN] Would create VPC connector:"
    echo "  gcloud compute networks vpc-access connectors create $CONNECTOR_NAME \\"
    echo "    --region=$REGION \\"
    echo "    --network=default \\"
    echo "    --range=$IP_RANGE \\"
    echo "    --min-instances=2 \\"
    echo "    --max-instances=10 \\"
    echo "    --project=$PROJECT_ID"
    exit 0
fi

# Enable Compute API
log_info "Enabling required APIs..."
gcloud services enable compute.googleapis.com vpcaccess.googleapis.com --project="$PROJECT_ID" 2>/dev/null
log_success "APIs enabled"

# Create VPC connector
log_info "Creating VPC connector (this may take 5-10 minutes)..."
gcloud compute networks vpc-access connectors create "$CONNECTOR_NAME" \
    --region="$REGION" \
    --network=default \
    --range="$IP_RANGE" \
    --min-instances=2 \
    --max-instances=10 \
    --project="$PROJECT_ID"

log_success "VPC connector created successfully"

echo ""
echo "✅ VPC Connector Configuration:"
echo "   Name: projects/$PROJECT_ID/locations/$REGION/connectors/$CONNECTOR_NAME"
echo ""
echo "📝 Next Steps:"
echo "1. Update app.yaml with VPC connector:"
echo "   vpc_access_connector:"
echo "     name: \"projects/$PROJECT_ID/locations/$REGION/connectors/$CONNECTOR_NAME\""
echo ""
echo "2. Deploy application: ./scripts/deploy-gcp.sh"
echo ""
