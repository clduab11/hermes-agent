"""Environment variable validation and sanitization for enterprise security."""

import os
import re
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum

import structlog

logger = structlog.get_logger()


class ValidationLevel(Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationRule:
    """Environment variable validation rule."""
    name: str
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    required: bool = False
    production_required: bool = False
    allowed_values: Optional[Set[str]] = None
    forbidden_values: Optional[Set[str]] = None
    description: str = ""
    security_level: ValidationLevel = ValidationLevel.INFO
    validate_format: bool = True
    mask_in_logs: bool = False


@dataclass
class ValidationResult:
    """Result of environment variable validation."""
    variable: str
    value: Optional[str]
    is_valid: bool
    level: ValidationLevel
    message: str
    rule_name: str
    suggestions: List[str]


class EnvironmentValidator:
    """Enterprise-grade environment variable validator."""

    def __init__(self):
        self.validation_rules: Dict[str, ValidationRule] = {}
        self.custom_validators: Dict[str, callable] = {}
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Setup default validation rules for common environment variables."""

        # Core application settings
        self.add_rule(ValidationRule(
            name="DEBUG",
            allowed_values={"true", "false", "1", "0"},
            description="Debug mode flag",
            security_level=ValidationLevel.WARNING
        ))

        self.add_rule(ValidationRule(
            name="DEMO_MODE",
            allowed_values={"true", "false", "1", "0"},
            description="Demo mode flag",
            security_level=ValidationLevel.WARNING
        ))

        self.add_rule(ValidationRule(
            name="ENVIRONMENT",
            allowed_values={"development", "staging", "production", "test"},
            description="Deployment environment",
            required=True,
            security_level=ValidationLevel.ERROR
        ))

        # API Configuration
        self.add_rule(ValidationRule(
            name="API_HOST",
            pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$|^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*$",
            description="API host address",
            security_level=ValidationLevel.WARNING
        ))

        self.add_rule(ValidationRule(
            name="API_PORT",
            pattern=r"^[1-9]\d{0,4}$",
            description="API port number (1-65535)",
            security_level=ValidationLevel.ERROR
        ))

        # Security-critical variables
        self.add_rule(ValidationRule(
            name="OPENAI_API_KEY",
            pattern=r"^sk-[A-Za-z0-9]{48}$",
            min_length=51,
            max_length=51,
            production_required=True,
            description="OpenAI API key",
            security_level=ValidationLevel.CRITICAL,
            mask_in_logs=True
        ))

        self.add_rule(ValidationRule(
            name="JWT_PRIVATE_KEY",
            min_length=200,  # Minimum for reasonable RSA private key
            production_required=True,
            description="JWT signing private key",
            security_level=ValidationLevel.CRITICAL,
            mask_in_logs=True
        ))

        self.add_rule(ValidationRule(
            name="JWT_PUBLIC_KEY",
            min_length=100,  # Minimum for reasonable RSA public key
            production_required=True,
            description="JWT verification public key",
            security_level=ValidationLevel.CRITICAL,
            mask_in_logs=True
        ))

        # Database URLs
        self.add_rule(ValidationRule(
            name="DATABASE_URL",
            pattern=r"^(postgresql|postgres|mysql|sqlite)://.*",
            description="Database connection URL",
            security_level=ValidationLevel.ERROR,
            mask_in_logs=True
        ))

        self.add_rule(ValidationRule(
            name="REDIS_URL",
            pattern=r"^redis://.*",
            description="Redis connection URL",
            security_level=ValidationLevel.WARNING
        ))

        # Third-party API keys
        self.add_rule(ValidationRule(
            name="GITHUB_TOKEN",
            pattern=r"^gh[ps]_[A-Za-z0-9]{36}$",
            description="GitHub personal access token",
            security_level=ValidationLevel.WARNING,
            mask_in_logs=True
        ))

        self.add_rule(ValidationRule(
            name="STRIPE_API_KEY",
            pattern=r"^(sk|pk)_(test_|live_)?[A-Za-z0-9]{24,}$",
            description="Stripe API key",
            security_level=ValidationLevel.ERROR,
            mask_in_logs=True
        ))

        self.add_rule(ValidationRule(
            name="SUPABASE_SERVICE_ROLE_KEY",
            min_length=100,
            description="Supabase service role key",
            security_level=ValidationLevel.WARNING,
            mask_in_logs=True
        ))

        # Secrets management
        self.add_rule(ValidationRule(
            name="SECRETS_PROVIDER",
            allowed_values={"env", "gcp", "aws", "azure", "vault"},
            description="Secrets provider backend",
            security_level=ValidationLevel.INFO
        ))

        self.add_rule(ValidationRule(
            name="SECRETS_AUDIT_ENABLED",
            allowed_values={"true", "false", "1", "0"},
            description="Enable secrets audit logging",
            security_level=ValidationLevel.WARNING
        ))

        # Security configuration
        self.add_rule(ValidationRule(
            name="CORS_ALLOW_ORIGINS",
            forbidden_values={"*"},  # Wildcard not allowed in production
            description="CORS allowed origins",
            security_level=ValidationLevel.ERROR
        ))

        # Audit and compliance
        self.add_rule(ValidationRule(
            name="AUDIT_LOGGING",
            allowed_values={"true", "false", "1", "0"},
            description="Enable audit logging",
            security_level=ValidationLevel.WARNING
        ))

    def add_rule(self, rule: ValidationRule):
        """Add a validation rule."""
        self.validation_rules[rule.name] = rule

    def add_custom_validator(self, variable_name: str, validator_func: callable):
        """Add a custom validation function for a variable."""
        self.custom_validators[variable_name] = validator_func

    def validate_variable(self, name: str, value: Optional[str] = None) -> ValidationResult:
        """Validate a single environment variable."""
        if value is None:
            value = os.getenv(name)

        rule = self.validation_rules.get(name)
        if not rule:
            # No rule defined, just check if it exists
            return ValidationResult(
                variable=name,
                value=self._mask_value(name, value) if rule and rule.mask_in_logs else value,
                is_valid=True,
                level=ValidationLevel.INFO,
                message="No validation rule defined",
                rule_name="default",
                suggestions=[]
            )

        return self._validate_against_rule(name, value, rule)

    def _validate_against_rule(self, name: str, value: Optional[str], rule: ValidationRule) -> ValidationResult:
        """Validate a variable against a specific rule."""
        suggestions = []
        is_valid = True
        messages = []
        level = ValidationLevel.INFO

        # Check if required
        if rule.required and not value:
            return ValidationResult(
                variable=name,
                value=None,
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Required variable {name} is not set",
                rule_name=rule.name,
                suggestions=[f"Set {name} environment variable"]
            )

        # Check if production required
        is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
        if rule.production_required and is_production and not value:
            return ValidationResult(
                variable=name,
                value=None,
                is_valid=False,
                level=ValidationLevel.CRITICAL,
                message=f"Production-required variable {name} is not set",
                rule_name=rule.name,
                suggestions=[f"Set {name} for production deployment"]
            )

        if not value:
            # Variable is not set but not required
            return ValidationResult(
                variable=name,
                value=None,
                is_valid=True,
                level=ValidationLevel.INFO,
                message=f"Optional variable {name} is not set",
                rule_name=rule.name,
                suggestions=[]
            )

        # Length validation
        if rule.min_length and len(value) < rule.min_length:
            is_valid = False
            level = max(level, rule.security_level)
            messages.append(f"Value too short (minimum {rule.min_length} characters)")
            suggestions.append(f"Ensure {name} has at least {rule.min_length} characters")

        if rule.max_length and len(value) > rule.max_length:
            is_valid = False
            level = max(level, rule.security_level)
            messages.append(f"Value too long (maximum {rule.max_length} characters)")
            suggestions.append(f"Ensure {name} has at most {rule.max_length} characters")

        # Pattern validation
        if rule.pattern and rule.validate_format:
            if not re.match(rule.pattern, value):
                is_valid = False
                level = max(level, rule.security_level)
                messages.append("Value does not match expected format")
                suggestions.append(f"Check {name} format: {rule.description}")

        # Allowed values validation
        if rule.allowed_values:
            if value not in rule.allowed_values:
                is_valid = False
                level = max(level, rule.security_level)
                messages.append(f"Value not in allowed list: {', '.join(rule.allowed_values)}")
                suggestions.append(f"Set {name} to one of: {', '.join(rule.allowed_values)}")

        # Forbidden values validation
        if rule.forbidden_values:
            if value in rule.forbidden_values:
                is_valid = False
                level = max(level, rule.security_level)
                messages.append(f"Value is forbidden: {value}")
                suggestions.append(f"Change {name} from forbidden value")

        # Custom validation
        if name in self.custom_validators:
            try:
                custom_result = self.custom_validators[name](value)
                if not custom_result:
                    is_valid = False
                    level = max(level, rule.security_level)
                    messages.append("Failed custom validation")
            except Exception as e:
                is_valid = False
                level = ValidationLevel.ERROR
                messages.append(f"Custom validation error: {str(e)}")

        # Security-specific checks
        if rule.security_level == ValidationLevel.CRITICAL:
            # Additional security checks for critical variables
            if self._is_weak_value(value):
                is_valid = False
                level = ValidationLevel.CRITICAL
                messages.append("Value appears to be weak or commonly used")
                suggestions.append(f"Use a strong, unique value for {name}")

        display_value = self._mask_value(name, value) if rule.mask_in_logs else value
        message = "; ".join(messages) if messages else "Validation passed"

        return ValidationResult(
            variable=name,
            value=display_value,
            is_valid=is_valid,
            level=level,
            message=message,
            rule_name=rule.name,
            suggestions=suggestions
        )

    def validate_all(self) -> Dict[str, Any]:
        """Validate all environment variables with defined rules."""
        results = []
        summary = {
            "total_variables": 0,
            "valid_variables": 0,
            "errors": 0,
            "warnings": 0,
            "critical_issues": 0,
            "production_ready": True
        }

        is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"

        for rule_name, rule in self.validation_rules.items():
            result = self.validate_variable(rule_name)
            results.append(result)

            summary["total_variables"] += 1

            if result.is_valid:
                summary["valid_variables"] += 1
            else:
                if result.level == ValidationLevel.ERROR:
                    summary["errors"] += 1
                    summary["production_ready"] = False
                elif result.level == ValidationLevel.WARNING:
                    summary["warnings"] += 1
                elif result.level == ValidationLevel.CRITICAL:
                    summary["critical_issues"] += 1
                    summary["production_ready"] = False

        # Check for undefined critical variables in environment
        for var_name, var_value in os.environ.items():
            if var_name not in self.validation_rules:
                # Check if it looks like a sensitive variable
                if self._looks_sensitive(var_name):
                    result = ValidationResult(
                        variable=var_name,
                        value=self._mask_value(var_name, var_value),
                        is_valid=True,
                        level=ValidationLevel.INFO,
                        message="Undefined sensitive variable detected",
                        rule_name="auto-detect",
                        suggestions=[f"Consider adding validation rule for {var_name}"]
                    )
                    results.append(result)

        return {
            "validation_timestamp": "utcnow().isoformat()",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "is_production": is_production,
            "summary": summary,
            "results": [self._result_to_dict(r) for r in results],
            "recommendations": self._generate_recommendations(results, is_production)
        }

    def _result_to_dict(self, result: ValidationResult) -> Dict[str, Any]:
        """Convert ValidationResult to dictionary."""
        return {
            "variable": result.variable,
            "value": result.value,
            "is_valid": result.is_valid,
            "level": result.level.value,
            "message": result.message,
            "rule_name": result.rule_name,
            "suggestions": result.suggestions
        }

    def _generate_recommendations(self, results: List[ValidationResult], is_production: bool) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        error_count = sum(1 for r in results if not r.is_valid and r.level == ValidationLevel.ERROR)
        critical_count = sum(1 for r in results if not r.is_valid and r.level == ValidationLevel.CRITICAL)

        if critical_count > 0:
            recommendations.append(f"Address {critical_count} critical security issues before deployment")

        if error_count > 0:
            recommendations.append(f"Fix {error_count} configuration errors")

        if is_production:
            # Production-specific recommendations
            debug_enabled = os.getenv("DEBUG", "false").lower() == "true"
            if debug_enabled:
                recommendations.append("Disable DEBUG mode in production")

            cors_origins = os.getenv("CORS_ALLOW_ORIGINS")
            if not cors_origins:
                recommendations.append("Set explicit CORS origins for production")

            secrets_provider = os.getenv("SECRETS_PROVIDER", "env")
            if secrets_provider == "env":
                recommendations.append("Consider using cloud secrets provider for production")

        return recommendations

    def _is_weak_value(self, value: str) -> bool:
        """Check if a value appears to be weak."""
        weak_patterns = [
            r"^(test|demo|example|sample|default).*$",
            r"^.*(123|password|secret|admin|user).*$",
            r"^.{1,7}$"  # Very short values
        ]

        value_lower = value.lower()
        return any(re.match(pattern, value_lower) for pattern in weak_patterns)

    def _looks_sensitive(self, var_name: str) -> bool:
        """Check if a variable name suggests it contains sensitive data."""
        sensitive_keywords = [
            "key", "secret", "token", "password", "credential", "auth",
            "api", "private", "cert", "ssl", "tls", "encryption"
        ]

        name_lower = var_name.lower()
        return any(keyword in name_lower for keyword in sensitive_keywords)

    def _mask_value(self, var_name: str, value: Optional[str]) -> Optional[str]:
        """Mask sensitive values for logging."""
        if not value:
            return None

        if self._looks_sensitive(var_name) or len(value) > 20:
            if len(value) <= 8:
                return "***"
            return value[:3] + "***" + value[-2:]

        return value

    def export_validation_report(self, file_path: str):
        """Export validation report to file."""
        validation_results = self.validate_all()

        report = f"""
# Environment Variable Validation Report
Generated: {validation_results['validation_timestamp']}
Environment: {validation_results['environment']}

## Summary
- Total Variables: {validation_results['summary']['total_variables']}
- Valid Variables: {validation_results['summary']['valid_variables']}
- Errors: {validation_results['summary']['errors']}
- Warnings: {validation_results['summary']['warnings']}
- Critical Issues: {validation_results['summary']['critical_issues']}
- Production Ready: {'✅' if validation_results['summary']['production_ready'] else '❌'}

## Issues Found
"""

        for result in validation_results['results']:
            if not result['is_valid']:
                level_emoji = {
                    'error': '❌',
                    'warning': '⚠️',
                    'critical': '🔥',
                    'info': 'ℹ️'
                }
                emoji = level_emoji.get(result['level'], 'ℹ️')

                report += f"""
{emoji} **{result['variable']}** ({result['level'].upper()})
   Message: {result['message']}
   Suggestions: {', '.join(result['suggestions']) if result['suggestions'] else 'None'}
"""

        if validation_results['recommendations']:
            report += "\n## Recommendations\n"
            for rec in validation_results['recommendations']:
                report += f"- {rec}\n"

        with open(file_path, 'w') as f:
            f.write(report)

        logger.info(f"Validation report exported to {file_path}")


# Global validator instance
env_validator = EnvironmentValidator()


# Convenience functions
def validate_environment() -> Dict[str, Any]:
    """Validate all environment variables."""
    return env_validator.validate_all()


def validate_variable(name: str, value: Optional[str] = None) -> ValidationResult:
    """Validate a single environment variable."""
    return env_validator.validate_variable(name, value)


def is_production_ready() -> bool:
    """Check if environment is ready for production."""
    results = validate_environment()
    return results['summary']['production_ready']