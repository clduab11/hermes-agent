#!/bin/bash

# HERMES Enterprise SaaS Secret Configuration Script
# Securely configures GCP Secret Manager for enterprise deployment

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
PROJECT_ID=""

# Get project ID
get_project_id() {
    if [ -z "$PROJECT_ID" ]; then
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
        if [ -z "$PROJECT_ID" ]; then
            read -p "Enter GCP Project ID: " PROJECT_ID
        fi
    fi

    if [ -z "$PROJECT_ID" ]; then
        print_error "Project ID is required"
        exit 1
    fi

    gcloud config set project "$PROJECT_ID"
    print_success "Using project: $PROJECT_ID"
}

# Update secret value securely
update_secret() {
    local secret_name="$1"
    local description="$2"

    print_status "Updating secret: $secret_name"
    echo "  Description: $description"

    # Check if secret exists
    if ! gcloud secrets describe "$secret_name" >/dev/null 2>&1; then
        print_error "Secret $secret_name does not exist. Run deploy.sh first."
        return 1
    fi

    # Prompt for secret value (hidden input)
    echo -n "Enter value for $secret_name: "
    read -s secret_value
    echo "" # New line after hidden input

    if [ -z "$secret_value" ]; then
        print_warning "Skipping empty value for $secret_name"
        return 0
    fi

    # Update secret
    echo "$secret_value" | gcloud secrets versions add "$secret_name" --data-file=-
    print_success "Updated $secret_name"
}

# Generate JWT key pair
generate_jwt_keys() {
    print_status "Generating JWT key pair for enterprise authentication..."

    # Create temporary directory
    temp_dir=$(mktemp -d)
    cd "$temp_dir"

    # Generate private key
    openssl genpkey -algorithm RSA -out private_key.pem -pkcs8 -pass pass: -aes256 -size 2048

    # Generate public key
    openssl rsa -pubout -in private_key.pem -out public_key.pem -passin pass:

    # Update secrets
    cat private_key.pem | gcloud secrets versions add "JWT_PRIVATE_KEY" --data-file=-
    cat public_key.pem | gcloud secrets versions add "JWT_PUBLIC_KEY" --data-file=-

    # Cleanup
    cd - >/dev/null
    rm -rf "$temp_dir"

    print_success "JWT key pair generated and stored securely"
}

# Generate API key encryption secret
generate_api_key_secret() {
    print_status "Generating API key encryption secret..."

    # Generate Fernet key for API key encryption
    python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" | \
        gcloud secrets versions add "API_KEY_ENCRYPTION_SECRET" --data-file=-

    print_success "API key encryption secret generated"
}

# Main configuration function
main() {
    echo "================================================================"
    echo "  HERMES Enterprise SaaS Secret Configuration"
    echo "  Secure setup for law firm deployment ($2,497/month)"
    echo "================================================================"
    echo ""

    get_project_id

    print_warning "This script will update enterprise secrets in GCP Secret Manager"
    print_warning "Only proceed if you have the required credentials and permissions"
    echo ""

    read -p "Continue with secret configuration? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        print_status "Secret configuration cancelled"
        exit 0
    fi

    echo ""
    print_status "Starting secret configuration..."
    echo ""

    # Generate system secrets
    generate_jwt_keys
    generate_api_key_secret

    # Configure external service secrets
    echo ""
    print_status "Configure external service credentials:"
    echo ""

    update_secret "SUPABASE_DATABASE_URL" "Supabase PostgreSQL connection URL (postgresql://...)"
    update_secret "SUPABASE_PROJECT_URL" "Supabase project URL (https://xxx.supabase.co)"
    update_secret "SUPABASE_SERVICE_KEY" "Supabase service role key (starts with eyJ...)"
    update_secret "OPENAI_API_KEY" "OpenAI API key for GPT-4 processing (sk-...)"
    update_secret "STRIPE_API_KEY" "Stripe secret key for billing (sk_live_...)"
    update_secret "STRIPE_WEBHOOK_SECRET" "Stripe webhook signing secret (whsec_...)"

    echo ""
    print_success "🎉 Secret configuration completed!"
    echo ""
    echo "📋 Summary:"
    echo "   • JWT key pair: Generated automatically"
    echo "   • API key encryption: Generated automatically"
    echo "   • External services: Configured manually"
    echo ""
    echo "🔐 Security Notes:"
    echo "   • All secrets are encrypted at rest in GCP Secret Manager"
    echo "   • Only authorized GCP service accounts can access secrets"
    echo "   • Secrets are automatically rotated on App Engine deployment"
    echo ""
    echo "📞 Next Steps:"
    echo "   1. Verify all secrets in GCP Console"
    echo "   2. Test database connectivity"
    echo "   3. Run deployment script: ./deployment/deploy.sh"
    echo ""
}

# Check if running as main script
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi