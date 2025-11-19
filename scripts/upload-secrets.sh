#!/bin/bash

# ====================================================================
# HERMES Secrets Upload Script
# ====================================================================
# Uploads secrets from .env.secrets to GCP Secret Manager.
# Automatically creates secrets if they don't exist and grants access
# to the App Engine service account.
#
# Usage:
#   ./scripts/upload-secrets.sh [--dry-run] [--project PROJECT_ID]
#
# Options:
#   --dry-run: Show what would be done without making changes
#   --project: Specify GCP project ID (default: from gcloud config)
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - .env.secrets file exists (run ./scripts/generate-secrets.sh first)
#   - Secret Manager API enabled
#   - Appropriate IAM permissions
# ====================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse arguments
DRY_RUN=false
PROJECT_ID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --project)
            PROJECT_ID="$2"
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Usage: $0 [--dry-run] [--project PROJECT_ID]"
            exit 1
            ;;
    esac
done

# ====================================================================
# Check Prerequisites
# ====================================================================

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI not found"
        echo "Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
        log_error "Not authenticated with gcloud"
        echo "Run: gcloud auth login"
        exit 1
    fi
    
    # Get or verify project ID
    if [ -z "$PROJECT_ID" ]; then
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
        if [ -z "$PROJECT_ID" ]; then
            log_error "No GCP project set"
            echo "Either:"
            echo "  1. Set default: gcloud config set project YOUR_PROJECT_ID"
            echo "  2. Specify: $0 --project YOUR_PROJECT_ID"
            exit 1
        fi
    fi
    
    log_info "Using project: $PROJECT_ID"
    
    # Check .env.secrets exists
    if [ ! -f ".env.secrets" ]; then
        log_error ".env.secrets file not found"
        echo "Generate secrets first: ./scripts/generate-secrets.sh"
        exit 1
    fi
    
    # Check Secret Manager API is enabled
    if ! gcloud services list --enabled --project="$PROJECT_ID" --filter="name:secretmanager.googleapis.com" --format="value(name)" | grep -q "secretmanager"; then
        log_warning "Secret Manager API not enabled"
        echo "Enabling Secret Manager API..."
        if [ "$DRY_RUN" = false ]; then
            gcloud services enable secretmanager.googleapis.com --project="$PROJECT_ID"
            log_success "Secret Manager API enabled"
        else
            log_info "[DRY-RUN] Would enable Secret Manager API"
        fi
    fi
    
    log_success "Prerequisites validated"
}

# ====================================================================
# Parse .env.secrets File
# ====================================================================

parse_secrets_file() {
    log_info "Parsing .env.secrets..."
    
    declare -g -A SECRETS
    
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        
        # Remove quotes and whitespace
        value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e 's/^[ \t]*//' -e 's/[ \t]*$//')
        
        # Skip if value is empty or looks like a comment
        [[ -z "$value" ]] && continue
        [[ "$value" =~ ^#.*$ ]] && continue
        
        # Store secret
        SECRETS[$key]="$value"
    done < .env.secrets
    
    log_success "Parsed ${#SECRETS[@]} secrets from .env.secrets"
}

# ====================================================================
# Upload Secrets to GCP
# ====================================================================

upload_secret() {
    local secret_name="$1"
    local secret_value="$2"
    
    # Create temporary file for multi-line secrets
    local temp_file=$(mktemp)
    echo -n "$secret_value" > "$temp_file"
    
    # Check if secret exists
    local exists=false
    if gcloud secrets describe "$secret_name" --project="$PROJECT_ID" &>/dev/null; then
        exists=true
    fi
    
    if [ "$DRY_RUN" = true ]; then
        if [ "$exists" = true ]; then
            log_info "[DRY-RUN] Would update secret: $secret_name"
        else
            log_info "[DRY-RUN] Would create secret: $secret_name"
        fi
    else
        if [ "$exists" = true ]; then
            # Add new version to existing secret
            log_info "Updating secret: $secret_name"
            gcloud secrets versions add "$secret_name" \
                --data-file="$temp_file" \
                --project="$PROJECT_ID" \
                >/dev/null 2>&1
            log_success "Updated: $secret_name"
        else
            # Create new secret
            log_info "Creating secret: $secret_name"
            gcloud secrets create "$secret_name" \
                --data-file="$temp_file" \
                --project="$PROJECT_ID" \
                --replication-policy="automatic" \
                >/dev/null 2>&1
            log_success "Created: $secret_name"
        fi
    fi
    
    # Clean up temp file
    rm -f "$temp_file"
}

# ====================================================================
# Grant Access to App Engine Service Account
# ====================================================================

grant_service_account_access() {
    local secret_name="$1"
    local service_account="$PROJECT_ID@appspot.gserviceaccount.com"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would grant access to $service_account for $secret_name"
        return
    fi
    
    # Check if access is already granted
    local has_access=false
    if gcloud secrets get-iam-policy "$secret_name" --project="$PROJECT_ID" --format="value(bindings.members)" 2>/dev/null | grep -q "$service_account"; then
        has_access=true
    fi
    
    if [ "$has_access" = false ]; then
        log_info "Granting access to App Engine service account..."
        gcloud secrets add-iam-policy-binding "$secret_name" \
            --member="serviceAccount:$service_account" \
            --role="roles/secretmanager.secretAccessor" \
            --project="$PROJECT_ID" \
            >/dev/null 2>&1
        log_success "Granted access: $secret_name"
    fi
}

# ====================================================================
# Validate Uploads
# ====================================================================

validate_uploads() {
    log_info "Validating uploaded secrets..."
    
    local failed_count=0
    
    for secret_name in "${!SECRETS[@]}"; do
        if ! gcloud secrets describe "$secret_name" --project="$PROJECT_ID" &>/dev/null; then
            log_error "Validation failed: $secret_name not found"
            ((failed_count++))
        fi
    done
    
    if [ $failed_count -eq 0 ]; then
        log_success "All secrets validated successfully"
        return 0
    else
        log_error "$failed_count secrets failed validation"
        return 1
    fi
}

# ====================================================================
# Summary Report
# ====================================================================

show_summary() {
    local created=$1
    local updated=$2
    local failed=$3
    
    echo ""
    echo "=================================================================="
    echo "              Secrets Upload Summary"
    echo "=================================================================="
    echo ""
    echo "📊 Statistics:"
    echo "  ✅ Created: $created"
    echo "  🔄 Updated: $updated"
    echo "  ❌ Failed:  $failed"
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY-RUN MODE: No actual changes were made"
        echo "  Re-run without --dry-run to apply changes"
        echo ""
    else
        log_success "Secrets uploaded to GCP Secret Manager"
        echo ""
        echo "📝 Next Steps:"
        echo ""
        echo "1️⃣  Verify secrets in GCP Console:"
        echo "   https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID"
        echo ""
        echo "2️⃣  Configure app.yaml to use Secret Manager:"
        echo "   env_variables:"
        echo "     SECRETS_PROVIDER: \"gcp\""
        echo "     GCP_PROJECT_ID: \"$PROJECT_ID\""
        echo ""
        echo "3️⃣  Test secret access (optional):"
        echo "   gcloud secrets versions access latest --secret=\"OPENAI_API_KEY\""
        echo ""
        echo "4️⃣  Continue with deployment:"
        echo "   ./scripts/deploy-gcp.sh"
        echo ""
    fi
}

# ====================================================================
# Main Execution
# ====================================================================

main() {
    echo "🔐 HERMES Secrets Upload Script"
    if [ "$DRY_RUN" = true ]; then
        log_warning "Running in DRY-RUN mode"
    fi
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Parse secrets file
    parse_secrets_file
    
    # Upload each secret
    local created=0
    local updated=0
    local failed=0
    
    echo ""
    log_info "Uploading secrets to GCP Secret Manager..."
    echo ""
    
    for secret_name in "${!SECRETS[@]}"; do
        # Check if exists before upload
        local exists=false
        if gcloud secrets describe "$secret_name" --project="$PROJECT_ID" &>/dev/null; then
            exists=true
        fi
        
        # Upload secret
        if upload_secret "$secret_name" "${SECRETS[$secret_name]}"; then
            if [ "$exists" = true ]; then
                ((updated++))
            else
                ((created++))
            fi
            
            # Grant access to service account (only for new secrets)
            if [ "$exists" = false ]; then
                grant_service_account_access "$secret_name"
            fi
        else
            log_error "Failed to upload: $secret_name"
            ((failed++))
        fi
    done
    
    # Validate uploads (skip in dry-run)
    if [ "$DRY_RUN" = false ]; then
        echo ""
        validate_uploads
    fi
    
    # Show summary
    show_summary $created $updated $failed
    
    # Exit with appropriate code
    if [ $failed -gt 0 ]; then
        exit 1
    fi
}

# Run main function
main "$@"
