#!/bin/bash

# HERMES Production Validation Script
# Validates that all components are ready for secure cloud deployment

set -euo pipefail

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

# Validation counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Track validation results
validate_check() {
    local check_name="$1"
    local check_result="$2"
    local check_message="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    case "$check_result" in
        "PASS")
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            log_success "$check_name: $check_message"
            ;;
        "FAIL")
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            log_error "$check_name: $check_message"
            ;;
        "WARN")
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
            log_warning "$check_name: $check_message"
            ;;
    esac
}

# Check Python environment
validate_python_environment() {
    log_info "Validating Python environment..."
    
    # Check Python version
    if python3 --version | grep -q "Python 3.1[1-2]"; then
        validate_check "Python Version" "PASS" "Python 3.11+ detected"
    else
        validate_check "Python Version" "FAIL" "Python 3.11+ required for production"
    fi
    
    # Check if virtual environment is recommended
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        validate_check "Virtual Environment" "PASS" "Virtual environment active"
    else
        validate_check "Virtual Environment" "WARN" "Virtual environment recommended for production"
    fi
}

# Validate dependencies
validate_dependencies() {
    log_info "Validating dependencies..."
    
    if [[ -f "requirements.txt" ]]; then
        validate_check "Requirements File" "PASS" "requirements.txt found"
        
        # Check for security vulnerabilities (if safety is available)
        if command -v safety >/dev/null 2>&1; then
            if safety check --file requirements.txt --output text | grep -q "No known security vulnerabilities found"; then
                validate_check "Security Scan" "PASS" "No security vulnerabilities found"
            else
                validate_check "Security Scan" "WARN" "Potential security vulnerabilities detected - review manually"
            fi
        else
            validate_check "Security Scan" "WARN" "Safety not installed - run 'pip install safety' to check for vulnerabilities"
        fi
    else
        validate_check "Requirements File" "FAIL" "requirements.txt not found"
    fi
}

# Validate configuration files
validate_configuration() {
    log_info "Validating configuration files..."
    
    # Check app.yaml
    if [[ -f "app.yaml" ]]; then
        validate_check "App Engine Config" "PASS" "app.yaml found"
        
        # Check for production settings
        if grep -q "DEBUG.*false" app.yaml && grep -q "DEMO_MODE.*false" app.yaml; then
            validate_check "Production Mode" "PASS" "Debug and demo modes disabled"
        else
            validate_check "Production Mode" "FAIL" "Debug or demo mode still enabled in app.yaml"
        fi
        
        # Check for proper resource allocation
        if grep -q "memory_gb.*[4-9]" app.yaml; then
            validate_check "Memory Allocation" "PASS" "Adequate memory allocation (4GB+)"
        else
            validate_check "Memory Allocation" "WARN" "Consider increasing memory allocation for production workloads"
        fi
    else
        validate_check "App Engine Config" "FAIL" "app.yaml not found"
    fi
    
    # Check security.yaml
    if [[ -f "security.yaml" ]]; then
        validate_check "Security Config" "PASS" "security.yaml found"
    else
        validate_check "Security Config" "FAIL" "security.yaml not found"
    fi
    
    # Check pyproject.toml
    if [[ -f "pyproject.toml" ]]; then
        validate_check "Project Config" "PASS" "pyproject.toml found"
    else
        validate_check "Project Config" "WARN" "pyproject.toml not found - consider adding for project metadata"
    fi
}

# Validate environment variables
validate_environment_variables() {
    log_info "Validating environment variables..."
    
    # Check if .env.production exists
    if [[ -f ".env.production" ]]; then
        validate_check "Production Environment" "PASS" ".env.production template found"
    else
        validate_check "Production Environment" "WARN" ".env.production template not found"
    fi
    
    # Check for critical environment variables in templates
    local required_vars=(
        "OPENAI_API_KEY"
        "JWT_PRIVATE_KEY"
        "JWT_PUBLIC_KEY"
        "DATABASE_URL"
        "SUPABASE_URL"
        "SUPABASE_SERVICE_ROLE_KEY"
    )
    
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if ! grep -q "$var" .env.production 2>/dev/null; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -eq 0 ]]; then
        validate_check "Required Variables" "PASS" "All critical environment variables documented"
    else
        validate_check "Required Variables" "FAIL" "Missing variables: ${missing_vars[*]}"
    fi
}

# Validate security implementation
validate_security() {
    log_info "Validating security implementation..."
    
    # Check for security modules
    if [[ -d "hermes/security" ]]; then
        validate_check "Security Module" "PASS" "Security module directory found"
        
        # Check for specific security files
        local security_files=(
            "hermes/security/secure_config.py"
            "hermes/security/config_validator.py"
            "hermes/security/secrets_manager.py"
        )
        
        local missing_security_files=()
        for file in "${security_files[@]}"; do
            if [[ ! -f "$file" ]]; then
                missing_security_files+=("$file")
            fi
        done
        
        if [[ ${#missing_security_files[@]} -eq 0 ]]; then
            validate_check "Security Files" "PASS" "All security implementation files found"
        else
            validate_check "Security Files" "FAIL" "Missing security files: ${missing_security_files[*]}"
        fi
    else
        validate_check "Security Module" "FAIL" "Security module directory not found"
    fi
    
    # Check for HTTPS enforcement
    if grep -q "secure: always" app.yaml 2>/dev/null; then
        validate_check "HTTPS Enforcement" "PASS" "HTTPS enforcement configured"
    else
        validate_check "HTTPS Enforcement" "FAIL" "HTTPS enforcement not configured in app.yaml"
    fi
}

# Validate deployment scripts
validate_deployment_scripts() {
    log_info "Validating deployment scripts..."
    
    local deployment_scripts=(
        "scripts/deploy-gcp.sh"
        "deployment/setup-secrets.sh"
    )
    
    for script in "${deployment_scripts[@]}"; do
        if [[ -f "$script" ]]; then
            validate_check "$(basename "$script")" "PASS" "Deployment script found"
            
            # Check if script is executable
            if [[ -x "$script" ]]; then
                validate_check "$(basename "$script") Permissions" "PASS" "Script is executable"
            else
                validate_check "$(basename "$script") Permissions" "WARN" "Script should be executable - run 'chmod +x $script'"
            fi
        else
            validate_check "$(basename "$script")" "FAIL" "Deployment script not found"
        fi
    done
}

# Validate static files and assets
validate_static_files() {
    log_info "Validating static files..."
    
    if [[ -d "static" ]]; then
        validate_check "Static Directory" "PASS" "Static files directory found"
        
        # Check for required static files
        if [[ -f "index.html" ]] || [[ -f "static/index.html" ]]; then
            validate_check "Landing Page" "PASS" "Landing page found"
        else
            validate_check "Landing Page" "WARN" "Landing page not found - may affect demo accessibility"
        fi
    else
        validate_check "Static Directory" "WARN" "Static files directory not found - will be created during deployment"
    fi
}

# Validate database migrations
validate_database() {
    log_info "Validating database configuration..."
    
    if [[ -d "alembic" ]]; then
        validate_check "Database Migrations" "PASS" "Alembic migrations directory found"
        
        # Check for alembic.ini
        if [[ -f "alembic.ini" ]]; then
            validate_check "Alembic Config" "PASS" "alembic.ini configuration found"
        else
            validate_check "Alembic Config" "FAIL" "alembic.ini not found"
        fi
    else
        validate_check "Database Migrations" "FAIL" "Alembic migrations directory not found"
    fi
}

# Check cloud deployment readiness
validate_cloud_readiness() {
    log_info "Validating cloud deployment readiness..."
    
    # Check if gcloud CLI is available
    if command -v gcloud >/dev/null 2>&1; then
        validate_check "Google Cloud SDK" "PASS" "gcloud CLI available"
        
        # Check if authenticated
        if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
            validate_check "GCP Authentication" "PASS" "Google Cloud authenticated"
        else
            validate_check "GCP Authentication" "FAIL" "Google Cloud authentication required - run 'gcloud auth login'"
        fi
    else
        validate_check "Google Cloud SDK" "FAIL" "gcloud CLI not installed"
    fi
    
    # Check for Dockerfile (should not exist for SaaS deployment)
    if [[ -f "Dockerfile" ]] || [[ -f "dockerfile" ]]; then
        validate_check "Docker Files" "FAIL" "Docker files found - remove for SaaS-only deployment"
    else
        validate_check "Docker Files" "PASS" "No Docker files found (SaaS deployment only)"
    fi
}

# Generate validation report
generate_report() {
    echo ""
    echo "=================================================================="
    echo "              HERMES PRODUCTION VALIDATION REPORT"
    echo "=================================================================="
    echo ""
    
    local success_rate=$(( (PASSED_CHECKS * 100) / TOTAL_CHECKS ))
    
    echo "📊 VALIDATION SUMMARY:"
    echo "  Total Checks: $TOTAL_CHECKS"
    echo "  ✅ Passed: $PASSED_CHECKS"
    echo "  ❌ Failed: $FAILED_CHECKS"
    echo "  ⚠️  Warnings: $WARNING_CHECKS"
    echo "  📈 Success Rate: ${success_rate}%"
    echo ""
    
    if [[ $FAILED_CHECKS -eq 0 ]]; then
        if [[ $WARNING_CHECKS -eq 0 ]]; then
            log_success "🎉 PRODUCTION READY - All checks passed!"
            echo "✅ Your HERMES deployment is ready for secure cloud hosting."
            echo "🚀 Proceed with deployment using: ./scripts/deploy-gcp.sh"
        else
            log_warning "⚠️  MOSTLY READY - Address warnings for optimal deployment"
            echo "🔧 Consider addressing the warnings above for best practices."
            echo "🚀 You can proceed with deployment, but review warnings first."
        fi
    else
        log_error "❌ NOT READY FOR PRODUCTION"
        echo "🛠️  Please address the failed checks before deploying."
        echo "📋 Review the errors above and run this script again."
        
        # Exit with error code if there are failures
        exit 1
    fi
    
    echo ""
    echo "📞 Support: If you need assistance, contact support@parallax-ai.app"
    echo "📚 Documentation: Check DEPLOYMENT_GUIDE.md for detailed instructions"
    echo ""
}

# Main validation function
main() {
    echo "🔍 Starting HERMES Production Validation..."
    echo "🏛️  Ensuring deployment readiness for law firm clients"
    echo ""
    
    # Run all validation checks
    validate_python_environment
    validate_dependencies
    validate_configuration
    validate_environment_variables
    validate_security
    validate_deployment_scripts
    validate_static_files
    validate_database
    validate_cloud_readiness
    
    # Generate final report
    generate_report
}

# Run validation if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi