#!/bin/bash

# ====================================================================
# HERMES Secret Generation Script
# ====================================================================
# Automatically generates cryptographic keys and secrets required for
# HERMES deployment. Outputs to .env.secrets file.
#
# Usage:
#   ./scripts/generate-secrets.sh
#
# Output:
#   .env.secrets - Contains all generated secrets
#
# Security: DO NOT commit .env.secrets to version control!
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

# ====================================================================
# Check Prerequisites
# ====================================================================

check_dependencies() {
    log_info "Checking dependencies..."
    
    local missing_deps=()
    
    # Check OpenSSL
    if ! command -v openssl &> /dev/null; then
        missing_deps+=("openssl")
    fi
    
    # Check Python3
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Check base64
    if ! command -v base64 &> /dev/null; then
        missing_deps+=("base64")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        echo ""
        echo "Install instructions:"
        echo "  Ubuntu/Debian: sudo apt-get install openssl python3 coreutils"
        echo "  macOS:         brew install openssl python3"
        echo "  Windows:       Install Git Bash or WSL"
        exit 1
    fi
    
    log_success "All dependencies found"
}

# ====================================================================
# Generate JWT Keys (RSA 2048-bit)
# ====================================================================

generate_jwt_keys() {
    log_info "Generating JWT RSA key pair (2048-bit)..."
    
    local temp_dir=$(mktemp -d)
    cd "$temp_dir"
    
    # Generate private key
    openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048 2>/dev/null
    
    # Generate public key
    openssl rsa -pubout -in private_key.pem -out public_key.pem 2>/dev/null
    
    # Convert to single-line format with \n markers (for .env compatibility)
    JWT_PRIVATE_KEY=$(awk 'NF {sub(/\r/, ""); printf "%s\\n",$0;}' private_key.pem)
    JWT_PUBLIC_KEY=$(awk 'NF {sub(/\r/, ""); printf "%s\\n",$0;}' public_key.pem)
    
    # Clean up
    cd - > /dev/null
    rm -rf "$temp_dir"
    
    log_success "JWT keys generated"
}

# ====================================================================
# Generate Fernet Encryption Keys
# ====================================================================

generate_fernet_key() {
    log_info "Generating Fernet encryption key for API keys..."
    
    API_KEY_ENCRYPTION_SECRET=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    
    log_success "API key encryption secret generated"
}

generate_clio_encryption_key() {
    log_info "Generating Fernet encryption key for Clio tokens..."
    
    CLIO_TOKEN_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    
    log_success "Clio token encryption key generated"
}

# ====================================================================
# Output Secrets to File
# ====================================================================

write_secrets_file() {
    log_info "Writing secrets to .env.secrets..."
    
    local output_file=".env.secrets"
    
    # Create file with header
    cat > "$output_file" << 'EOF'
# ====================================================================
# HERMES Generated Secrets
# ====================================================================
# Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
#
# ⚠️  SECURITY WARNING:
# - DO NOT commit this file to version control
# - DO NOT share this file with unauthorized parties
# - Store securely (password manager, encrypted storage)
# - For production, upload to GCP Secret Manager:
#     ./scripts/upload-secrets.sh
#
# ====================================================================

EOF
    
    # Add actual timestamp
    sed -i "s/\$(date -u +\"%Y-%m-%d %H:%M:%S UTC\")/$(date -u +"%Y-%m-%d %H:%M:%S UTC")/" "$output_file"
    
    # Add JWT keys
    cat >> "$output_file" << EOF
# JWT Authentication Keys (RSA 2048-bit)
# Used for signing and verifying access tokens
JWT_PRIVATE_KEY="$JWT_PRIVATE_KEY"
JWT_PUBLIC_KEY="$JWT_PUBLIC_KEY"

EOF
    
    # Add encryption secrets
    cat >> "$output_file" << EOF
# API Key Encryption Secret (Fernet)
# Used for encrypting API keys in database
API_KEY_ENCRYPTION_SECRET=$API_KEY_ENCRYPTION_SECRET

EOF
    
    # Add Clio encryption key
    cat >> "$output_file" << EOF
# Clio Token Encryption Key (Fernet)
# Used for encrypting Clio OAuth tokens
CLIO_TOKEN_ENCRYPTION_KEY=$CLIO_TOKEN_ENCRYPTION_KEY

EOF
    
    # Add placeholder for other secrets
    cat >> "$output_file" << 'EOF'
# ====================================================================
# External Service Secrets
# ====================================================================
# Fill in these values manually from your service providers:
# See docs/services/ for setup instructions for each service.

# Supabase Database
# Get from: https://supabase.com/dashboard → Settings → Database & API
# SUPABASE_DATABASE_URL=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres
# SUPABASE_URL=https://xxxxx.supabase.co
# SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# OpenAI API
# Get from: https://platform.openai.com/api-keys
# OPENAI_API_KEY=sk-...

# Stripe Billing
# Get from: https://dashboard.stripe.com/apikeys
# STRIPE_API_KEY=sk_live_... (or sk_test_... for testing)
# STRIPE_WEBHOOK_SECRET=whsec_...

# Clio Integration (Optional)
# Get from: https://app.clio.com/api/v4/documentation
# CLIO_CLIENT_SECRET=your-clio-client-secret

# ====================================================================
# Next Steps:
# ====================================================================
# 1. Fill in external service secrets above (uncomment and add values)
# 2. Copy these secrets to .env for local development:
#      cat .env.secrets >> .env
# 3. For production, upload to GCP Secret Manager:
#      ./scripts/upload-secrets.sh
# 4. DO NOT commit .env or .env.secrets to git!
# ====================================================================
EOF
    
    # Set restrictive permissions
    chmod 600 "$output_file"
    
    log_success "Secrets written to $output_file"
}

# ====================================================================
# Display Instructions
# ====================================================================

show_instructions() {
    echo ""
    echo "=================================================================="
    echo "           HERMES Secrets Generated Successfully!"
    echo "=================================================================="
    echo ""
    log_success "Generated secrets written to: .env.secrets"
    echo ""
    echo "📋 Generated Secrets:"
    echo "  ✅ JWT Private Key (RSA 2048-bit)"
    echo "  ✅ JWT Public Key (RSA 2048-bit)"
    echo "  ✅ API Key Encryption Secret (Fernet)"
    echo "  ✅ Clio Token Encryption Key (Fernet)"
    echo ""
    echo "📝 Next Steps:"
    echo ""
    echo "1️⃣  Fill in External Service Secrets"
    echo "   Edit .env.secrets and add:"
    echo "   - Supabase credentials (see docs/services/supabase-setup.md)"
    echo "   - OpenAI API key (see docs/services/openai-setup.md)"
    echo "   - Stripe API keys (see docs/services/stripe-setup.md)"
    echo ""
    echo "2️⃣  For Local Development"
    echo "   Copy secrets to .env:"
    echo "   $ cat .env.secrets >> .env"
    echo ""
    echo "3️⃣  For Production Deployment"
    echo "   Upload to GCP Secret Manager:"
    echo "   $ ./scripts/upload-secrets.sh"
    echo ""
    echo "⚠️  Security Reminders:"
    echo "   - DO NOT commit .env.secrets to git"
    echo "   - DO NOT share this file with unauthorized parties"
    echo "   - Store securely (password manager, encrypted storage)"
    echo "   - Delete after uploading to production (or store encrypted)"
    echo ""
    echo "📚 Documentation:"
    echo "   - Setup guides: docs/services/"
    echo "   - Deployment: DEPLOYMENT.md"
    echo "   - Prerequisites: DEPLOYMENT_PREREQUISITES.md"
    echo ""
}

# ====================================================================
# Main Execution
# ====================================================================

main() {
    echo "🔐 HERMES Secret Generation Script"
    echo "Generating cryptographic keys and secrets..."
    echo ""
    
    # Check if .env.secrets already exists
    if [ -f ".env.secrets" ]; then
        log_warning ".env.secrets already exists"
        read -p "Overwrite? This will generate NEW keys (old keys will be lost) [y/N]: " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            log_info "Cancelled. Existing .env.secrets preserved."
            exit 0
        fi
        log_warning "Overwriting .env.secrets..."
    fi
    
    # Check dependencies
    check_dependencies
    
    # Generate secrets
    generate_jwt_keys
    generate_fernet_key
    generate_clio_encryption_key
    
    # Write to file
    write_secrets_file
    
    # Show instructions
    show_instructions
}

# Run main function
main "$@"
