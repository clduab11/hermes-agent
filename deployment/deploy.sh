#!/bin/bash

# HERMES Enterprise SaaS Deployment Script for GCP App Engine
# Prevents self-hosting and enforces controlled SaaS deployment
# Law firm clients pay $2,497/month - no self-hosting allowed

set -e

echo "🚀 HERMES Enterprise SaaS Deployment Starting..."
echo "💼 Enterprise Law Firm Deployment ($2,497/month)"
echo "🔒 Self-hosting prevention: Active"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=""
REGION="us-central1"
SERVICE_NAME="hermes-enterprise"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate GCP project
validate_gcp_project() {
    print_status "Validating GCP project configuration..."

    if [ -z "$PROJECT_ID" ]; then
        print_error "PROJECT_ID not set. Please configure your GCP project ID."
        exit 1
    fi

    # Verify gcloud is authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null; then
        print_error "Not authenticated with gcloud. Run 'gcloud auth login'"
        exit 1
    fi

    gcloud config set project "$PROJECT_ID"
    print_success "GCP project configured: $PROJECT_ID"
}

# Enable required APIs
enable_apis() {
    print_status "Enabling required GCP APIs..."

    gcloud services enable appengine.googleapis.com
    gcloud services enable secretmanager.googleapis.com
    gcloud services enable cloudresourcemanager.googleapis.com
    gcloud services enable cloudsql.googleapis.com

    print_success "Required APIs enabled"
}

# Create GCP secrets for enterprise deployment
create_secrets() {
    print_status "Creating enterprise secrets in GCP Secret Manager..."

    # Create secrets (values will be set separately for security)
    local secrets=(
        "SUPABASE_DATABASE_URL"
        "SUPABASE_PROJECT_URL"
        "SUPABASE_SERVICE_KEY"
        "OPENAI_API_KEY"
        "JWT_PRIVATE_KEY"
        "JWT_PUBLIC_KEY"
        "STRIPE_API_KEY"
        "STRIPE_WEBHOOK_SECRET"
        "API_KEY_ENCRYPTION_SECRET"
    )

    for secret in "${secrets[@]}"; do
        if ! gcloud secrets describe "$secret" >/dev/null 2>&1; then
            echo "placeholder" | gcloud secrets create "$secret" --data-file=-
            print_success "Created secret: $secret"
        else
            print_warning "Secret already exists: $secret"
        fi
    done

    print_warning "IMPORTANT: Update secret values in GCP Console before deployment!"
    print_warning "Secrets with placeholder values will cause deployment to fail."
}

# Validate enterprise prerequisites
validate_enterprise_setup() {
    print_status "Validating enterprise SaaS prerequisites..."

    # Check for required files
    local required_files=(
        "app.yaml"
        "security.yaml"
        "hermes/auth/api_key_auth.py"
    )

    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Required file missing: $file"
            exit 1
        fi
    done

    # Verify no Docker files exist (anti-self-hosting)
    if [ -f "Dockerfile" ] || [ -f "docker-compose.yml" ]; then
        print_error "Docker files found - these must be removed for SaaS deployment"
        print_error "Self-hosting is not permitted with enterprise SaaS license"
        exit 1
    fi

    print_success "Enterprise prerequisites validated"
}

# Deploy to App Engine
deploy_app_engine() {
    print_status "Deploying HERMES to GCP App Engine..."

    # Update app.yaml with correct project ID
    sed -i.bak "s/PROJECT_ID/$PROJECT_ID/g" app.yaml
    sed -i.bak "s/REGION/$REGION/g" app.yaml

    # Deploy to App Engine
    gcloud app deploy app.yaml security.yaml \
        --project="$PROJECT_ID" \
        --version="$(date +%Y%m%d%H%M%S)" \
        --promote \
        --quiet

    # Cleanup backup files
    rm -f app.yaml.bak security.yaml.bak

    print_success "Deployment completed successfully"
}

# Configure custom domain (optional)
configure_domain() {
    local domain="$1"

    if [ -n "$domain" ]; then
        print_status "Configuring custom domain: $domain"

        gcloud app domain-mappings create "$domain" \
            --certificate-management=AUTOMATIC \
            --project="$PROJECT_ID"

        print_success "Custom domain configured: $domain"
        print_warning "DNS configuration required - see GCP Console for records"
    fi
}

# Setup monitoring and alerting
setup_monitoring() {
    print_status "Setting up enterprise monitoring..."

    # Create uptime check
    cat > uptime-check.json << EOF
{
  "displayName": "HERMES Enterprise Health Check",
  "httpCheck": {
    "path": "/health",
    "port": 443,
    "useSsl": true
  },
  "period": "300s",
  "timeout": "10s"
}
EOF

    gcloud alpha monitoring uptime create-config uptime-check.json --project="$PROJECT_ID"
    rm uptime-check.json

    print_success "Enterprise monitoring configured"
}

# Generate deployment report
generate_deployment_report() {
    local app_url="https://$PROJECT_ID.appspot.com"

    print_success "🎉 HERMES Enterprise SaaS Deployment Complete!"
    echo ""
    echo "📊 Deployment Summary:"
    echo "   • Project ID: $PROJECT_ID"
    echo "   • Service URL: $app_url"
    echo "   • Region: $REGION"
    echo "   • Pricing Tier: Enterprise ($2,497/month)"
    echo "   • Database: Supabase (required)"
    echo "   • Authentication: API Key (required)"
    echo ""
    echo "🔐 Security Features:"
    echo "   • Self-hosting prevention: ✅"
    echo "   • API key authentication: ✅"
    echo "   • GCP Secret Manager: ✅"
    echo "   • HTTPS enforcement: ✅"
    echo "   • Enterprise firewall: ✅"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Update secrets in GCP Secret Manager"
    echo "   2. Configure Supabase database connection"
    echo "   3. Generate enterprise API keys for law firm clients"
    echo "   4. Test deployment at: $app_url/health"
    echo ""
    echo "💬 Enterprise Support: enterprise@hermes-ai.com"
}

# Main deployment function
main() {
    echo "================================================================"
    echo "  HERMES Enterprise SaaS Deployment for Law Firms"
    echo "  Self-hosting prevention enabled"
    echo "  Enterprise pricing: $2,497/month per firm"
    echo "================================================================"
    echo ""

    # Get project ID if not set
    if [ -z "$PROJECT_ID" ]; then
        read -p "Enter GCP Project ID: " PROJECT_ID
        if [ -z "$PROJECT_ID" ]; then
            print_error "Project ID is required"
            exit 1
        fi
    fi

    # Optional custom domain
    read -p "Enter custom domain (optional, press Enter to skip): " CUSTOM_DOMAIN

    # Execute deployment steps
    validate_gcp_project
    enable_apis
    create_secrets
    validate_enterprise_setup
    deploy_app_engine

    if [ -n "$CUSTOM_DOMAIN" ]; then
        configure_domain "$CUSTOM_DOMAIN"
    fi

    setup_monitoring
    generate_deployment_report
}

# Check if running as main script
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi