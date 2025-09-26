"""
Secure Configuration Module for HERMES SaaS
Copyright (c) 2024 Parallax Analytics LLC. All rights reserved.

This module enforces secure configuration and prevents local development bypasses.
"""

import os
import logging
import hashlib
from typing import Dict, Any, List, Optional
from .license_enforcer import license_enforcer

logger = logging.getLogger(__name__)

# CRITICAL: Prohibited environment variables that enable self-hosting
PROHIBITED_ENV_VARS = {
    "DEBUG",
    "DEMO_MODE",
    "DEVELOPMENT",
    "LOCAL_MODE",
    "BYPASS_LICENSE",
    "SKIP_VALIDATION",
    "ALLOW_SELF_HOST",
    "DEV_OVERRIDE",
    "TEST_MODE",
    "HERMES_DEV_LICENSE_BYPASS"  # Remove development bypass
}

# Required production environment variables
REQUIRED_PRODUCTION_ENV_VARS = {
    "HERMES_LICENSE_KEY",
    "HERMES_TENANT_ID",
    "HERMES_API_BASE",
    "DATABASE_URL",
    "REDIS_URL"
}

# Allowed configuration patterns for SaaS deployment
ALLOWED_CONFIG_PATTERNS = {
    "api_base": [
        "https://api.hermes.parallax-ai.app",
        "https://api-staging.hermes.parallax-ai.app"
    ],
    "websocket_base": [
        "wss://ws.hermes.parallax-ai.app",
        "wss://ws-staging.hermes.parallax-ai.app"
    ],
    "database_hosts": [
        ".supabase.co",
        ".googleusercontent.com",
        ".amazonaws.com"  # Only cloud databases allowed
    ]
}

class ConfigSecurityViolation(Exception):
    """Raised when insecure configuration is detected."""
    pass

class SecureConfigValidator:
    """Validates and enforces secure configuration for SaaS deployment."""

    def __init__(self):
        self.violations = []
        self.warnings = []

    def validate_production_config(self) -> Dict[str, Any]:
        """Validate configuration for production SaaS deployment."""

        self.violations.clear()
        self.warnings.clear()

        logger.info("Validating secure production configuration...")

        # Check 1: Remove prohibited environment variables
        self._check_prohibited_env_vars()

        # Check 2: Validate required production variables
        self._check_required_production_vars()

        # Check 3: Validate API endpoints
        self._validate_api_endpoints()

        # Check 4: Validate database configuration
        self._validate_database_config()

        # Check 5: Validate network configuration
        self._validate_network_config()

        # Generate security report
        security_score = self._calculate_security_score()

        result = {
            "secure": len(self.violations) == 0,
            "security_score": security_score,
            "violations": self.violations,
            "warnings": self.warnings,
            "timestamp": "2024-01-15T00:00:00Z"
        }

        if not result["secure"]:
            logger.critical(f"Configuration security violations detected: {self.violations}")
            raise ConfigSecurityViolation(f"Insecure configuration: {self.violations}")

        logger.info(f"Configuration validated - Security score: {security_score}/100")
        return result

    def _check_prohibited_env_vars(self):
        """Remove and check for prohibited environment variables."""
        found_prohibited = []

        for var_name in PROHIBITED_ENV_VARS:
            if var_name in os.environ:
                found_prohibited.append(var_name)
                # CRITICAL: Remove the variable to prevent bypass
                del os.environ[var_name]
                logger.warning(f"Removed prohibited environment variable: {var_name}")

        if found_prohibited:
            self.violations.append(f"Prohibited environment variables found and removed: {found_prohibited}")

    def _check_required_production_vars(self):
        """Check for required production environment variables."""
        missing_vars = []

        for var_name in REQUIRED_PRODUCTION_ENV_VARS:
            if not os.getenv(var_name):
                missing_vars.append(var_name)

        if missing_vars:
            self.violations.append(f"Missing required production variables: {missing_vars}")

    def _validate_api_endpoints(self):
        """Validate API endpoints are pointing to authorized SaaS infrastructure."""
        api_base = os.getenv("HERMES_API_BASE", "")
        ws_base = os.getenv("HERMES_WS_BASE", "")

        if api_base and api_base not in ALLOWED_CONFIG_PATTERNS["api_base"]:
            self.violations.append(f"Unauthorized API endpoint: {api_base}")

        if ws_base and ws_base not in ALLOWED_CONFIG_PATTERNS["websocket_base"]:
            self.violations.append(f"Unauthorized WebSocket endpoint: {ws_base}")

    def _validate_database_config(self):
        """Validate database configuration points to cloud providers only."""
        database_url = os.getenv("DATABASE_URL", "")
        redis_url = os.getenv("REDIS_URL", "")

        # Check database URL
        if database_url:
            if any(pattern in database_url for pattern in ["localhost", "127.0.0.1", "0.0.0.0"]):
                self.violations.append("Local database URLs are prohibited")

            authorized_host = any(
                host_pattern in database_url
                for host_pattern in ALLOWED_CONFIG_PATTERNS["database_hosts"]
            )
            if not authorized_host:
                self.violations.append(f"Unauthorized database host in: {database_url[:50]}...")

        # Check Redis URL
        if redis_url:
            if any(pattern in redis_url for pattern in ["localhost", "127.0.0.1"]):
                self.violations.append("Local Redis URLs are prohibited")

    def _validate_network_config(self):
        """Validate network configuration is secure."""
        api_host = os.getenv("API_HOST", "127.0.0.1")

        # Only allow secure host bindings in production
        if api_host in ["0.0.0.0", "::0"]:
            self.warnings.append("Binding to all interfaces - ensure proper firewall configuration")

    def _calculate_security_score(self) -> int:
        """Calculate security score based on configuration."""
        base_score = 100

        # Deduct points for violations (major)
        score = base_score - (len(self.violations) * 25)

        # Deduct points for warnings (minor)
        score = score - (len(self.warnings) * 5)

        return max(0, min(100, score))

    def enforce_secure_runtime_config(self):
        """Enforce secure configuration at runtime."""

        # Disable debug features in production
        self._disable_debug_features()

        # Validate license continuously
        if not license_enforcer.is_license_valid():
            raise ConfigSecurityViolation("Invalid license detected")

        # Check for runtime tampering
        self._check_runtime_tampering()

    def _disable_debug_features(self):
        """Disable debug and development features."""
        # Override common debug settings
        debug_vars = ["DEBUG", "FLASK_DEBUG", "DJANGO_DEBUG", "DEVELOPMENT"]

        for var in debug_vars:
            if os.getenv(var):
                os.environ[var] = "False"
                logger.info(f"Disabled debug variable: {var}")

    def _check_runtime_tampering(self):
        """Check for runtime configuration tampering."""
        # Verify critical configuration hasn't been modified
        current_license = os.getenv("HERMES_LICENSE_KEY", "")
        current_tenant = os.getenv("HERMES_TENANT_ID", "")

        if not current_license or not current_tenant:
            raise ConfigSecurityViolation("License configuration was tampered with")

    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for HTTP responses."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "X-Hermes-License": "SaaS-Only",
            "X-Deployment-Mode": "Production-Secure"
        }

    def validate_deployment_integrity(self) -> bool:
        """Validate deployment integrity and prevent tampering."""
        try:
            # Check critical file integrity
            critical_files = [
                "hermes/security/license_enforcer.py",
                "hermes/security/secure_config.py",
                "hermes/main.py"
            ]

            for file_path in critical_files:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        # Simple integrity check - in production this would be more sophisticated
                        if b"HERMES" not in content:
                            logger.warning(f"Potential tampering detected in {file_path}")
                            return False

            return True

        except Exception as e:
            logger.error(f"Integrity check failed: {e}")
            return False

# Global secure config validator instance
secure_config_validator = SecureConfigValidator()

# Initialization function to be called at startup
def initialize_secure_config():
    """Initialize secure configuration enforcement."""
    logger.info("Initializing secure configuration enforcement...")

    try:
        # Validate production configuration
        config_result = secure_config_validator.validate_production_config()

        # Enforce runtime security
        secure_config_validator.enforce_secure_runtime_config()

        # Validate deployment integrity
        if not secure_config_validator.validate_deployment_integrity():
            raise ConfigSecurityViolation("Deployment integrity check failed")

        logger.info("Secure configuration initialized successfully")
        return config_result

    except Exception as e:
        logger.critical(f"Secure configuration initialization failed: {e}")
        raise

def get_security_headers() -> Dict[str, str]:
    """Get security headers for responses."""
    return secure_config_validator.get_security_headers()

def validate_request_authorization(request_info: Dict[str, Any]) -> bool:
    """Validate request is from authorized source."""
    # Check if request is from authorized domain
    origin = request_info.get("origin", "")
    host = request_info.get("host", "")

    authorized_origins = [
        "https://app.hermes.parallax-ai.app",
        "https://api.hermes.parallax-ai.app"
    ]

    if origin and origin not in authorized_origins:
        logger.warning(f"Unauthorized origin: {origin}")
        return False

    return True