#!/bin/bash

# HERMES Enterprise SaaS - GCP Deployment Script
# This script automates the complete deployment of HERMES to Google App Engine
# with enterprise-grade security and secret management.

set -euo pipefail

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-hermes-legal-ai}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${GCP_SERVICE:-default}"
ENVIRONMENT="${ENVIRONMENT:-production}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        log_error "Google Cloud SDK is not installed. Please install it first."
        exit 1
    fi

    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null; then
        log_error "No active Google Cloud authentication found. Please run 'gcloud auth login'."
        exit 1
    fi

    # Set project
    gcloud config set project "$PROJECT_ID"

    log_success "Prerequisites validated"
}

# Enable required APIs
enable_apis() {
    log_info "Enabling required Google Cloud APIs..."

    local apis=(
        "appengine.googleapis.com"
        "cloudbuild.googleapis.com"
        "secretmanager.googleapis.com"
        "cloudresourcemanager.googleapis.com"
        "cloudmonitoring.googleapis.com"
        "cloudsql.googleapis.com"
        "redis.googleapis.com"
        "compute.googleapis.com"
    )

    for api in "${apis[@]}"; do
        log_info "Enabling $api..."
        gcloud services enable "$api" --project="$PROJECT_ID"
    done

    log_success "APIs enabled successfully"
}

# Create App Engine application if it doesn't exist
create_app_engine() {
    log_info "Checking App Engine application..."

    if ! gcloud app describe --project="$PROJECT_ID" &> /dev/null; then
        log_info "Creating App Engine application in region $REGION..."
        gcloud app create --region="$REGION" --project="$PROJECT_ID"
        log_success "App Engine application created"
    else
        log_info "App Engine application already exists"
    fi
}

# Create and configure secrets
setup_secrets() {
    log_info "Setting up Google Secret Manager secrets..."

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
        "CLIO_CLIENT_SECRET"
        "CLIO_TOKEN_ENCRYPTION_KEY"
    )

    for secret_name in "${secrets[@]}"; do
        # Check if secret exists
        if ! gcloud secrets describe "$secret_name" --project="$PROJECT_ID" &> /dev/null; then
            log_info "Creating secret: $secret_name"

            # For deployment, we'll create placeholder secrets that need to be updated manually
            echo "PLACEHOLDER_VALUE_UPDATE_MANUALLY" | gcloud secrets create "$secret_name" \
                --data-file=- \
                --project="$PROJECT_ID"

            log_warning "Created placeholder for $secret_name - UPDATE MANUALLY before deployment"
        else
            log_info "Secret $secret_name already exists"
        fi
    done

    log_success "Secrets configuration completed"
}

# Grant App Engine service account access to secrets
configure_secret_access() {
    log_info "Configuring secret access for App Engine..."

    # Get the App Engine service account
    local service_account="${PROJECT_ID}@appspot.gserviceaccount.com"

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
        "CLIO_CLIENT_SECRET"
        "CLIO_TOKEN_ENCRYPTION_KEY"
    )

    for secret_name in "${secrets[@]}"; do
        log_info "Granting access to $secret_name..."
        gcloud secrets add-iam-policy-binding "$secret_name" \
            --member="serviceAccount:$service_account" \
            --role="roles/secretmanager.secretAccessor" \
            --project="$PROJECT_ID"
    done

    log_success "Secret access configured"
}

# Create VPC connector for private database access
create_vpc_connector() {
    log_info "Creating VPC connector for secure database access..."

    local connector_name="hermes-connector"

    # Check if connector exists
    if ! gcloud compute networks vpc-access connectors describe "$connector_name" \
        --region="$REGION" --project="$PROJECT_ID" &> /dev/null; then

        log_info "Creating VPC access connector..."
        gcloud compute networks vpc-access connectors create "$connector_name" \
            --network=default \
            --range=10.8.0.0/28 \
            --region="$REGION" \
            --project="$PROJECT_ID"

        log_success "VPC connector created"
    else
        log_info "VPC connector already exists"
    fi
}

# Update app.yaml with correct project references
update_app_yaml() {
    log_info "Updating app.yaml with project-specific configuration..."

    # Create a temporary app.yaml with project ID substituted
    sed "s/PROJECT_ID/$PROJECT_ID/g; s/REGION/$REGION/g" app.yaml > app-deploy.yaml

    log_success "app.yaml updated for deployment"
}

# Validate deployment configuration
validate_deployment() {
    log_info "Validating deployment configuration..."

    # Check if app.yaml exists
    if [[ ! -f "app.yaml" ]]; then
        log_error "app.yaml not found in current directory"
        exit 1
    fi

    # Check if requirements.txt exists
    if [[ ! -f "requirements.txt" ]]; then
        log_error "requirements.txt not found in current directory"
        exit 1
    fi

    # Check if static directory exists
    if [[ ! -d "static" ]]; then
        log_warning "Static directory not found - creating basic structure"
        mkdir -p static/assets static/dashboard static/landing
    fi

    log_success "Deployment configuration validated"
}

# Deploy to App Engine
deploy_application() {
    log_info "Deploying HERMES to App Engine..."

    # Deploy the application
    gcloud app deploy app-deploy.yaml \
        --project="$PROJECT_ID" \
        --promote \
        --stop-previous-version \
        --quiet

    log_success "Application deployed successfully"

    # Get the deployed URL
    local app_url
    app_url=$(gcloud app describe --project="$PROJECT_ID" --format="value(defaultHostname)")

    log_success "HERMES is now available at: https://$app_url"
}

# Configure custom domain (if provided)
configure_domain() {
    local custom_domain="${CUSTOM_DOMAIN:-}"

    if [[ -n "$custom_domain" ]]; then
        log_info "Configuring custom domain: $custom_domain"

        # Map the custom domain
        gcloud app domain-mappings create "$custom_domain" \
            --project="$PROJECT_ID"

        log_success "Custom domain configured"
        log_info "Please update your DNS records to point to Google App Engine"
        log_info "Run 'gcloud app domain-mappings describe $custom_domain' for DNS details"
    fi
}

# Set up monitoring and alerting
configure_monitoring() {
    log_info "Configuring Cloud Monitoring..."

    # Create uptime check
    cat > uptime-check.json << EOF
{
  "displayName": "HERMES Health Check",
  "monitoredResource": {
    "type": "uptime_url",
    "labels": {
      "project_id": "$PROJECT_ID",
      "host": "$PROJECT_ID.appspot.com"
    }
  },
  "httpCheck": {
    "path": "/health",
    "port": 443,
    "useSsl": true
  },
  "period": "60s",
  "timeout": "10s"
}
EOF

    # Apply uptime check (requires gcloud alpha)
    if gcloud components list --filter="id:alpha" --format="value(id)" | grep -q alpha; then
        gcloud alpha monitoring uptime create --config-from-file=uptime-check.json \
            --project="$PROJECT_ID" || log_warning "Uptime check creation failed - configure manually"
    else
        log_warning "gcloud alpha components not installed - configure uptime checks manually"
    fi

    rm -f uptime-check.json

    log_success "Monitoring configuration completed"
}

# Main deployment function
main() {
    log_info "Starting HERMES Enterprise SaaS deployment to GCP..."
    log_info "Project: $PROJECT_ID"
    log_info "Region: $REGION"
    log_info "Environment: $ENVIRONMENT"

    check_prerequisites
    enable_apis
    create_app_engine
    setup_secrets
    configure_secret_access
    create_vpc_connector
    update_app_yaml
    validate_deployment
    deploy_application
    configure_domain
    configure_monitoring

    # Clean up temporary files
    rm -f app-deploy.yaml

    log_success "🎉 HERMES deployment completed successfully!"

    echo ""
    log_info "Next steps:"
    echo "1. Update all secrets in Google Secret Manager with actual values"
    echo "2. Configure your custom domain DNS records if using custom domain"
    echo "3. Set up SSL certificate for custom domain"
    echo "4. Configure monitoring alerts in Cloud Console"
    echo "5. Test the deployment at: https://$PROJECT_ID.appspot.com"
    echo ""
    log_info "For production readiness, ensure all placeholder secrets are updated!"
}

# Handle script termination
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"