#!/bin/bash

# HERMES Enterprise SaaS - Secret Management Script
# This script helps manage Google Cloud Secret Manager secrets for HERMES deployment

set -euo pipefail

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-hermes-legal-ai}"

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

# Show usage information
show_usage() {
    echo "HERMES Secret Management Tool"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  list                List all secrets and their status"
    echo "  create SECRET_NAME  Create a new secret (interactive)"
    echo "  update SECRET_NAME  Update an existing secret (interactive)"
    echo "  delete SECRET_NAME  Delete a secret"
    echo "  generate-keys       Generate JWT key pair"
    echo "  validate            Validate all required secrets exist"
    echo "  export-env          Export secrets to .env file (for local development)"
    echo ""
    echo "Options:"
    echo "  --project PROJECT_ID    Set GCP project ID"
    echo "  --help                  Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  GCP_PROJECT_ID    Google Cloud Project ID (default: hermes-legal-ai)"
}

# List all secrets
list_secrets() {
    log_info "Listing secrets for project: $PROJECT_ID"
    echo ""

    local required_secrets=(
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

    printf "%-25s %-10s %-20s\n" "SECRET NAME" "STATUS" "LAST UPDATED"
    printf "%-25s %-10s %-20s\n" "----------" "------" "------------"

    for secret in "${required_secrets[@]}"; do
        if gcloud secrets describe "$secret" --project="$PROJECT_ID" &> /dev/null; then
            local last_updated
            last_updated=$(gcloud secrets versions list "$secret" --project="$PROJECT_ID" --limit=1 --format="value(createTime)" | cut -d'T' -f1)
            printf "%-25s %-10s %-20s\n" "$secret" "EXISTS" "$last_updated"
        else
            printf "%-25s %-10s %-20s\n" "$secret" "MISSING" "N/A"
        fi
    done
}

# Create a new secret
create_secret() {
    local secret_name="$1"

    log_info "Creating secret: $secret_name"

    # Check if secret already exists
    if gcloud secrets describe "$secret_name" --project="$PROJECT_ID" &> /dev/null; then
        log_error "Secret $secret_name already exists. Use 'update' command instead."
        return 1
    fi

    # Get secret value securely
    echo -n "Enter value for $secret_name (input will be hidden): "
    read -s secret_value
    echo ""

    if [[ -z "$secret_value" ]]; then
        log_error "Secret value cannot be empty"
        return 1
    fi

    # Create the secret
    echo "$secret_value" | gcloud secrets create "$secret_name" \
        --data-file=- \
        --project="$PROJECT_ID"

    log_success "Secret $secret_name created successfully"
}

# Update an existing secret
update_secret() {
    local secret_name="$1"

    log_info "Updating secret: $secret_name"

    # Check if secret exists
    if ! gcloud secrets describe "$secret_name" --project="$PROJECT_ID" &> /dev/null; then
        log_error "Secret $secret_name does not exist. Use 'create' command instead."
        return 1
    fi

    # Get secret value securely
    echo -n "Enter new value for $secret_name (input will be hidden): "
    read -s secret_value
    echo ""

    if [[ -z "$secret_value" ]]; then
        log_error "Secret value cannot be empty"
        return 1
    fi

    # Add new version
    echo "$secret_value" | gcloud secrets versions add "$secret_name" \
        --data-file=- \
        --project="$PROJECT_ID"

    log_success "Secret $secret_name updated successfully"
}

# Delete a secret
delete_secret() {
    local secret_name="$1"

    log_warning "This will permanently delete the secret: $secret_name"
    echo -n "Are you sure? (yes/no): "
    read -r confirmation

    if [[ "$confirmation" != "yes" ]]; then
        log_info "Deletion cancelled"
        return 0
    fi

    gcloud secrets delete "$secret_name" --project="$PROJECT_ID" --quiet

    log_success "Secret $secret_name deleted successfully"
}

# Generate JWT key pair
generate_jwt_keys() {
    log_info "Generating RSA key pair for JWT authentication..."

    # Generate private key
    local private_key
    private_key=$(openssl genrsa 2048 2>/dev/null)

    # Generate public key
    local public_key
    public_key=$(echo "$private_key" | openssl rsa -pubout 2>/dev/null)

    # Store private key
    echo "$private_key" | gcloud secrets create "JWT_PRIVATE_KEY" \
        --data-file=- \
        --project="$PROJECT_ID" || \
    echo "$private_key" | gcloud secrets versions add "JWT_PRIVATE_KEY" \
        --data-file=- \
        --project="$PROJECT_ID"

    # Store public key
    echo "$public_key" | gcloud secrets create "JWT_PUBLIC_KEY" \
        --data-file=- \
        --project="$PROJECT_ID" || \
    echo "$public_key" | gcloud secrets versions add "JWT_PUBLIC_KEY" \
        --data-file=- \
        --project="$PROJECT_ID"

    log_success "JWT key pair generated and stored successfully"
}

# Validate all required secrets exist
validate_secrets() {
    log_info "Validating required secrets..."

    local required_secrets=(
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

    local missing_secrets=()
    local placeholder_secrets=()

    for secret in "${required_secrets[@]}"; do
        if ! gcloud secrets describe "$secret" --project="$PROJECT_ID" &> /dev/null; then
            missing_secrets+=("$secret")
        else
            # Check if it's a placeholder
            local secret_value
            secret_value=$(gcloud secrets versions access latest --secret="$secret" --project="$PROJECT_ID")
            if [[ "$secret_value" == "PLACEHOLDER_VALUE_UPDATE_MANUALLY" ]]; then
                placeholder_secrets+=("$secret")
            fi
        fi
    done

    if [[ ${#missing_secrets[@]} -eq 0 && ${#placeholder_secrets[@]} -eq 0 ]]; then
        log_success "All required secrets are present and configured"
        return 0
    fi

    if [[ ${#missing_secrets[@]} -gt 0 ]]; then
        log_error "Missing secrets:"
        for secret in "${missing_secrets[@]}"; do
            echo "  - $secret"
        done
    fi

    if [[ ${#placeholder_secrets[@]} -gt 0 ]]; then
        log_warning "Placeholder secrets that need to be updated:"
        for secret in "${placeholder_secrets[@]}"; do
            echo "  - $secret"
        done
    fi

    return 1
}

# Export secrets to .env file for local development
export_env() {
    log_info "Exporting secrets to .env file..."

    local env_file=".env.production"
    local required_secrets=(
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

    echo "# HERMES Production Secrets - Generated $(date)" > "$env_file"
    echo "# WARNING: Keep this file secure and never commit to version control" >> "$env_file"
    echo "" >> "$env_file"

    for secret in "${required_secrets[@]}"; do
        if gcloud secrets describe "$secret" --project="$PROJECT_ID" &> /dev/null; then
            local secret_value
            secret_value=$(gcloud secrets versions access latest --secret="$secret" --project="$PROJECT_ID")

            # Handle multiline secrets (like JWT keys)
            if [[ "$secret_value" == *$'\n'* ]]; then
                echo "${secret}='${secret_value}'" >> "$env_file"
            else
                echo "${secret}=${secret_value}" >> "$env_file"
            fi
        else
            echo "${secret}=MISSING_SECRET" >> "$env_file"
        fi
    done

    log_success "Secrets exported to $env_file"
    log_warning "Remember to keep this file secure and never commit it to version control"
}

# Main function
main() {
    local command="${1:-}"

    case "$command" in
        "list")
            list_secrets
            ;;
        "create")
            if [[ $# -lt 2 ]]; then
                log_error "Secret name is required for create command"
                show_usage
                exit 1
            fi
            create_secret "$2"
            ;;
        "update")
            if [[ $# -lt 2 ]]; then
                log_error "Secret name is required for update command"
                show_usage
                exit 1
            fi
            update_secret "$2"
            ;;
        "delete")
            if [[ $# -lt 2 ]]; then
                log_error "Secret name is required for delete command"
                show_usage
                exit 1
            fi
            delete_secret "$2"
            ;;
        "generate-keys")
            generate_jwt_keys
            ;;
        "validate")
            validate_secrets
            ;;
        "export-env")
            export_env
            ;;
        "--help"|"help"|"")
            show_usage
            ;;
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project)
            PROJECT_ID="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            # This is the command, pass it to main
            main "$@"
            exit 0
            ;;
    esac
done

# If no arguments provided, show usage
show_usage