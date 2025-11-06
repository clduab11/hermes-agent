"""Configuration validation and security checks for production deployment."""

import os
import re
import ipaddress
import socket
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from urllib.parse import urlparse
import json

import structlog
from .secrets_manager import secrets_manager, SecretValidationError

logger = structlog.get_logger()


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass


class SecurityViolation(Exception):
    """Raised when security policy is violated."""
    pass


class ConfigurationValidator:
    """Enterprise-grade configuration validator with security policy enforcement."""

    # Security policies for production environments
    SECURITY_POLICIES = {
        "require_https": True,
        "min_api_key_length": 20,
        "allow_localhost_in_production": False,
        "require_jwt_keys_in_production": True,
        "max_token_expiry_hours": 24,
        "require_audit_logging": True,
        "require_tls_1_3": True,
        "block_common_passwords": True,
        "require_strong_encryption": True
    }

    # Common weak passwords to block
    WEAK_PASSWORDS = {
        "password", "123456", "admin", "secret", "test", "demo",
        "changeme", "default", "guest", "user", "root"
    }

    # Dangerous configuration patterns
    DANGEROUS_PATTERNS = [
        r"password\s*=\s*['\"]?(admin|test|demo|123|password)['\"]?",
        r"secret\s*=\s*['\"]?(test|demo|secret)['\"]?",
        r"api_key\s*=\s*['\"]?(test|demo|sk-test)['\"]?",
    ]

    # Required environment variables for production
    PRODUCTION_REQUIRED_VARS = {
        "OPENAI_API_KEY": "OpenAI API key for LLM functionality",
        "JWT_PRIVATE_KEY": "Private key for JWT token signing",
        "JWT_PUBLIC_KEY": "Public key for JWT token verification",
    }

    # Optional but recommended for enterprise deployment
    ENTERPRISE_RECOMMENDED_VARS = {
        "SECRETS_PROVIDER": "Cloud secrets provider (gcp, aws, azure, vault)",
        "AUDIT_LOGGING": "Enable comprehensive audit logging",
        "REDIS_URL": "Redis cache for performance optimization",
        "DATABASE_URL": "Database connection for persistent storage",
        "SUPABASE_SERVICE_ROLE_KEY": "Supabase integration for legal data",
        "STRIPE_API_KEY": "Stripe integration for billing (if needed)"
    }

    def __init__(self):
        self.validation_errors: List[str] = []
        self.security_warnings: List[str] = []
        self.recommendations: List[str] = []
        self.is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"

    def validate_production_deployment(self) -> Dict[str, Any]:
        """Comprehensive validation for production deployment."""
        logger.info("Starting production deployment validation...")

        # Reset validation state
        self.validation_errors = []
        self.security_warnings = []
        self.recommendations = []

        # Run all validation checks
        self._validate_environment_variables()
        self._validate_security_policies()
        self._validate_network_configuration()
        self._validate_secrets_configuration()
        self._validate_database_configuration()
        self._validate_authentication_configuration()
        self._validate_tls_configuration()
        self._validate_audit_configuration()
        self._check_dangerous_patterns()
        self._validate_api_configurations()

        # Compile results
        results = {
            "validation_passed": len(self.validation_errors) == 0,
            "production_ready": len(self.validation_errors) == 0 and len(self.security_warnings) == 0,
            "timestamp": datetime.utcnow().isoformat(),
            "environment": "production" if self.is_production else "development",
            "debug_mode": self.debug_mode,
            "demo_mode": self.demo_mode,
            "errors": self.validation_errors,
            "security_warnings": self.security_warnings,
            "recommendations": self.recommendations,
            "secrets_health": secrets_manager.get_secrets_health_status(),
            "configuration_score": self._calculate_configuration_score()
        }

        # Log results
        if results["production_ready"]:
            logger.info("Production deployment validation PASSED")
        else:
            logger.error("Production deployment validation FAILED",
                        errors=self.validation_errors,
                        warnings=self.security_warnings)

        return results

    def _validate_environment_variables(self):
        """Validate required and recommended environment variables."""
        missing_required = []

        # Check required variables
        for var, description in self.PRODUCTION_REQUIRED_VARS.items():
            value = secrets_manager.get_secret(var)
            if not value:
                missing_required.append(f"{var} - {description}")

        if missing_required and self.is_production:
            self.validation_errors.extend([
                f"Missing required environment variable: {var}"
                for var in missing_required
            ])

        # Check recommended variables
        missing_recommended = []
        for var, description in self.ENTERPRISE_RECOMMENDED_VARS.items():
            value = secrets_manager.get_secret(var)
            if not value:
                missing_recommended.append(f"{var} - {description}")

        if missing_recommended:
            self.recommendations.extend([
                f"Consider setting: {var}"
                for var in missing_recommended
            ])

    def _validate_security_policies(self):
        """Validate security policy compliance."""

        # Check if production mode restrictions are enforced
        if self.is_production:
            if self.debug_mode:
                self.security_warnings.append(
                    "Debug mode is enabled in production environment"
                )

            if self.demo_mode:
                self.security_warnings.append(
                    "Demo mode is enabled in production environment"
                )

        # Check API host configuration
        api_host = os.getenv("API_HOST", "127.0.0.1")
        if api_host == "0.0.0.0" and self.is_production:
            self.validation_errors.append(
                "API is bound to 0.0.0.0 in production - this is a security risk. "
                "Bind to a specific interface (e.g., 127.0.0.1 with reverse proxy)"
            )

        # Check CORS configuration
        cors_origins = os.getenv("CORS_ALLOW_ORIGINS")
        if cors_origins == "*" and self.is_production:
            self.validation_errors.append(
                "CORS allows all origins (*) in production - security risk"
            )

    def _validate_network_configuration(self):
        """Validate network and endpoint configurations."""

        # Validate API host
        api_host = os.getenv("API_HOST", "127.0.0.1")
        try:
            ipaddress.ip_address(api_host)
            if ipaddress.ip_address(api_host).is_loopback and self.is_production:
                if not self.SECURITY_POLICIES["allow_localhost_in_production"]:
                    self.validation_errors.append(
                        "Localhost binding not allowed in production"
                    )
        except ValueError:
            # Might be a hostname
            try:
                socket.gethostbyname(api_host)
            except socket.gaierror:
                self.validation_errors.append(f"Invalid API host: {api_host}")

        # Validate port
        api_port = int(os.getenv("API_PORT", "8000"))
        if not 1 <= api_port <= 65535:
            self.validation_errors.append(f"Invalid API port: {api_port}")

        # Check for privileged port usage
        if api_port < 1024 and os.getuid() != 0:  # Unix-like systems
            self.security_warnings.append(
                f"Using privileged port {api_port} without root access may fail"
            )

    def _validate_secrets_configuration(self):
        """Validate secrets management configuration."""

        # Check secrets provider
        provider = os.getenv("SECRETS_PROVIDER", "env")
        if provider == "env" and self.is_production:
            self.recommendations.append(
                "Consider using cloud secrets provider (GCP, AWS, Azure, Vault) for production"
            )

        # Validate secrets provider configuration
        if provider in ["gcp", "aws", "azure", "vault"]:
            required_vars = {
                "gcp": ["GCP_PROJECT_ID"],
                "aws": [],  # Uses default AWS credentials
                "azure": ["AZURE_VAULT_URL"],
                "vault": ["VAULT_URL", "VAULT_TOKEN"]
            }

            for var in required_vars.get(provider, []):
                if not os.getenv(var):
                    self.validation_errors.append(
                        f"Missing required variable for {provider} secrets provider: {var}"
                    )

        # Check encryption configuration
        if os.getenv("SECRETS_ENCRYPT_CACHE", "true").lower() == "true":
            encryption_key = os.getenv("SECRETS_CACHE_ENCRYPTION_KEY")
            if not encryption_key and self.is_production:
                self.security_warnings.append(
                    "Cache encryption enabled but no persistent key configured"
                )

    def _validate_database_configuration(self):
        """Validate database configuration."""

        database_url = secrets_manager.get_secret("DATABASE_URL")
        if database_url:
            try:
                parsed = urlparse(database_url)

                # Check scheme
                if parsed.scheme not in ["postgresql", "postgres", "mysql", "sqlite"]:
                    self.security_warnings.append(
                        f"Unusual database scheme: {parsed.scheme}"
                    )

                # Check for localhost in production
                if parsed.hostname in ["localhost", "127.0.0.1", "::1"] and self.is_production:
                    self.security_warnings.append(
                        "Database using localhost in production environment"
                    )

                # Check for default ports
                default_ports = {"postgresql": 5432, "postgres": 5432, "mysql": 3306}
                expected_port = default_ports.get(parsed.scheme)
                if expected_port and parsed.port and parsed.port != expected_port:
                    self.recommendations.append(
                        f"Non-standard port {parsed.port} for {parsed.scheme} database"
                    )

            except Exception as e:
                self.validation_errors.append(f"Invalid database URL format: {str(e)}")

        # Validate Redis configuration
        redis_url = secrets_manager.get_secret("REDIS_URL")
        if redis_url:
            try:
                parsed = urlparse(redis_url)
                if parsed.scheme != "redis":
                    self.validation_errors.append("Redis URL must use redis:// scheme")
            except Exception as e:
                self.validation_errors.append(f"Invalid Redis URL format: {str(e)}")

    def _validate_authentication_configuration(self):
        """Validate JWT and authentication configuration."""

        # Check JWT keys
        private_key = secrets_manager.get_secret("JWT_PRIVATE_KEY")
        public_key = secrets_manager.get_secret("JWT_PUBLIC_KEY")

        if self.is_production and self.SECURITY_POLICIES["require_jwt_keys_in_production"]:
            if not private_key:
                self.validation_errors.append("JWT private key required for production")
            if not public_key:
                self.validation_errors.append("JWT public key required for production")

        # Validate JWT key formats
        if private_key:
            try:
                secrets_manager._validate_secret("JWT_PRIVATE_KEY", private_key)
            except SecretValidationError as e:
                self.validation_errors.append(f"Invalid JWT private key: {str(e)}")

        if public_key:
            try:
                secrets_manager._validate_secret("JWT_PUBLIC_KEY", public_key)
            except SecretValidationError as e:
                self.validation_errors.append(f"Invalid JWT public key: {str(e)}")

        # Check token expiration settings
        access_token_expire = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
        if access_token_expire > self.SECURITY_POLICIES["max_token_expiry_hours"] * 60:
            self.security_warnings.append(
                f"Access token expiry ({access_token_expire} minutes) exceeds security policy"
            )

    def _validate_tls_configuration(self):
        """Validate TLS and encryption configuration."""

        # Check if HTTPS is enforced
        if self.is_production and self.SECURITY_POLICIES["require_https"]:
            # This would typically be handled by reverse proxy (nginx, CloudFlare, etc.)
            self.recommendations.append(
                "Ensure HTTPS is enforced by reverse proxy or load balancer"
            )

        # Check TLS version requirements
        if self.SECURITY_POLICIES["require_tls_1_3"]:
            self.recommendations.append(
                "Ensure TLS 1.3 is enabled and TLS 1.0/1.1 are disabled"
            )

    def _validate_audit_configuration(self):
        """Validate audit logging configuration."""

        audit_enabled = os.getenv("AUDIT_LOGGING", "true").lower() == "true"

        if self.is_production and self.SECURITY_POLICIES["require_audit_logging"]:
            if not audit_enabled:
                self.validation_errors.append(
                    "Audit logging is required for production deployment"
                )

        # Check secrets audit configuration
        secrets_audit = os.getenv("SECRETS_AUDIT_ENABLED", "true").lower() == "true"
        if not secrets_audit and self.is_production:
            self.security_warnings.append(
                "Secrets audit logging is disabled in production"
            )

    def _check_dangerous_patterns(self):
        """Check for dangerous configuration patterns."""

        # Check environment variables for dangerous patterns
        for key, value in os.environ.items():
            if not value or key in secrets_manager.SENSITIVE_KEYS:
                continue

            value_lower = value.lower()

            # Check for weak passwords
            if any(weak in value_lower for weak in self.WEAK_PASSWORDS):
                self.security_warnings.append(
                    f"Potentially weak value detected in {key}"
                )

            # Check for dangerous patterns
            for pattern in self.DANGEROUS_PATTERNS:
                if re.search(pattern, f"{key}={value}", re.IGNORECASE):
                    self.security_warnings.append(
                        f"Dangerous pattern detected in {key}"
                    )

    def _validate_api_configurations(self):
        """Validate third-party API configurations."""

        # Validate OpenAI API key
        openai_key = secrets_manager.get_secret("OPENAI_API_KEY")
        if openai_key:
            try:
                secrets_manager._validate_secret("OPENAI_API_KEY", openai_key)
            except SecretValidationError as e:
                self.validation_errors.append(f"Invalid OpenAI API key: {str(e)}")

        # Validate Stripe configuration if present
        stripe_key = secrets_manager.get_secret("STRIPE_API_KEY")
        if stripe_key:
            if stripe_key.startswith("sk_test_") and self.is_production:
                self.validation_errors.append(
                    "Test Stripe key used in production environment"
                )
            elif not stripe_key.startswith(("sk_live_", "sk_test_")):
                self.validation_errors.append("Invalid Stripe API key format")

        # Validate GitHub token if present
        github_token = secrets_manager.get_secret("GITHUB_TOKEN")
        if github_token:
            try:
                secrets_manager._validate_secret("GITHUB_TOKEN", github_token)
            except SecretValidationError as e:
                self.validation_errors.append(f"Invalid GitHub token: {str(e)}")

    def _calculate_configuration_score(self) -> int:
        """Calculate configuration security score (0-100)."""
        total_checks = 20  # Approximate number of checks

        # Deduct points for errors and warnings
        error_penalty = len(self.validation_errors) * 10
        warning_penalty = len(self.security_warnings) * 5

        # Bonus for good practices
        bonus = 0
        if os.getenv("SECRETS_PROVIDER", "env") != "env":
            bonus += 10
        if os.getenv("SECRETS_AUDIT_ENABLED", "true").lower() == "true":
            bonus += 5
        if os.getenv("SECRETS_ENCRYPT_CACHE", "true").lower() == "true":
            bonus += 5

        score = max(0, min(100, 100 - error_penalty - warning_penalty + bonus))
        return score

    def generate_security_report(self) -> str:
        """Generate a comprehensive security report."""
        validation_results = self.validate_production_deployment()

        report = f"""
# HERMES Security Configuration Report
Generated: {validation_results['timestamp']}
Environment: {validation_results['environment']}
Configuration Score: {validation_results['configuration_score']}/100

## Overall Status
{'✅ PRODUCTION READY' if validation_results['production_ready'] else '❌ NOT PRODUCTION READY'}

## Validation Summary
- Errors: {len(self.validation_errors)}
- Security Warnings: {len(self.security_warnings)}
- Recommendations: {len(self.recommendations)}

## Secrets Management Health
- Provider: {validation_results['secrets_health']['provider']}
- Cache Encryption: {'✅' if validation_results['secrets_health']['cache_encryption_enabled'] else '❌'}
- Audit Logging: {'✅' if validation_results['secrets_health']['audit_enabled'] else '❌'}
- Tracked Secrets: {validation_results['secrets_health']['total_secrets_tracked']}
- Compromised Secrets: {validation_results['secrets_health']['compromised_secrets']}
- Secrets Needing Rotation: {validation_results['secrets_health']['secrets_needing_rotation']}
"""

        if self.validation_errors:
            report += "\n## ❌ Critical Errors\n"
            for error in self.validation_errors:
                report += f"- {error}\n"

        if self.security_warnings:
            report += "\n## ⚠️ Security Warnings\n"
            for warning in self.security_warnings:
                report += f"- {warning}\n"

        if self.recommendations:
            report += "\n## 💡 Recommendations\n"
            for rec in self.recommendations:
                report += f"- {rec}\n"

        report += "\n## Next Steps\n"
        if validation_results['production_ready']:
            report += "✅ Configuration is production-ready. Continue with deployment.\n"
        else:
            report += "❌ Address all critical errors before production deployment.\n"
            report += "⚠️ Review and resolve security warnings for optimal security.\n"

        return report

    def validate_environment_file(self, env_file_path: str) -> Dict[str, Any]:
        """Validate an environment file for security issues."""
        if not os.path.exists(env_file_path):
            return {"error": f"Environment file not found: {env_file_path}"}

        issues = []
        recommendations = []

        try:
            with open(env_file_path, 'r') as f:
                content = f.read()

                # Check for hardcoded secrets
                for pattern in self.DANGEROUS_PATTERNS:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        issues.append(f"Potential hardcoded secret detected: {match}")

                # Check for weak values
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.split('=', 1)
                        value = value.strip().strip('"').strip("'")

                        if value.lower() in self.WEAK_PASSWORDS:
                            issues.append(f"Line {i}: Weak value for {key}")

                        if len(value) < 8 and 'PASSWORD' in key.upper():
                            issues.append(f"Line {i}: Password too short for {key}")

                # Check for missing quotes around values with spaces
                for i, line in enumerate(lines, 1):
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.split('=', 1)
                        if ' ' in value and not (value.startswith('"') or value.startswith("'")):
                            recommendations.append(f"Line {i}: Consider quoting value for {key}")

        except Exception as e:
            return {"error": f"Failed to read environment file: {str(e)}"}

        return {
            "file_path": env_file_path,
            "issues": issues,
            "recommendations": recommendations,
            "is_safe": len(issues) == 0
        }


# Global validator instance
config_validator = ConfigurationValidator()


# Convenience functions
def validate_production_deployment() -> Dict[str, Any]:
    """Validate production deployment configuration."""
    return config_validator.validate_production_deployment()


def generate_security_report() -> str:
    """Generate comprehensive security report."""
    return config_validator.generate_security_report()


def validate_env_file(file_path: str) -> Dict[str, Any]:
    """Validate environment file for security issues."""
    return config_validator.validate_environment_file(file_path)