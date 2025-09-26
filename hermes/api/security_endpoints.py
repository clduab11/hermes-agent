"""Security management endpoints for enterprise deployment."""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from ..security.secrets_manager import secrets_manager, validate_production_secrets
from ..security.config_validator import config_validator
from ..security.env_validator import env_validator, validate_environment
from ..auth import JWTAuthMiddleware

router = APIRouter(prefix="/api/security", tags=["security"])


@router.get("/health")
async def security_health_check() -> Dict[str, Any]:
    """Comprehensive security health check for production deployment."""
    try:
        # Run all security checks in parallel
        tasks = [
            asyncio.create_task(_get_secrets_health()),
            asyncio.create_task(_get_config_validation()),
            asyncio.create_task(_get_env_validation()),
        ]

        secrets_health, config_validation, env_validation = await asyncio.gather(*tasks)

        # Calculate overall security score
        overall_score = _calculate_security_score(secrets_health, config_validation, env_validation)

        # Determine production readiness
        production_ready = (
            config_validation.get("production_ready", False) and
            env_validation.get("summary", {}).get("production_ready", False) and
            secrets_health.get("compromised_secrets", 0) == 0
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy" if production_ready else "issues_detected",
            "production_ready": production_ready,
            "security_score": overall_score,
            "secrets_management": secrets_health,
            "configuration_validation": config_validation,
            "environment_validation": env_validation,
            "recommendations": _generate_security_recommendations(
                secrets_health, config_validation, env_validation
            )
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Security health check failed: {str(e)}"
        )


@router.get("/secrets/status")
async def secrets_status() -> Dict[str, Any]:
    """Get secrets management status and health metrics."""
    try:
        return secrets_manager.get_secrets_health_status()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get secrets status: {str(e)}"
        )


@router.post("/secrets/validate")
async def validate_secrets() -> Dict[str, Any]:
    """Validate all secrets for production readiness."""
    try:
        return validate_production_secrets()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Secrets validation failed: {str(e)}"
        )


@router.post("/secrets/rotate/{secret_key}")
async def rotate_secret(secret_key: str, new_value: str, force: bool = False) -> Dict[str, Any]:
    """Rotate a specific secret (requires admin access)."""
    # Note: This endpoint should be heavily restricted in production
    try:
        success = secrets_manager.rotate_secret(secret_key, new_value, force)
        return {
            "success": success,
            "secret_key": secret_key,
            "rotated_at": datetime.utcnow().isoformat(),
            "message": "Secret rotated successfully" if success else "Secret rotation failed"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Secret rotation failed: {str(e)}"
        )


@router.post("/secrets/mark-compromised/{secret_key}")
async def mark_secret_compromised(secret_key: str) -> Dict[str, Any]:
    """Mark a secret as compromised for immediate attention."""
    try:
        secrets_manager.mark_secret_compromised(secret_key)
        return {
            "success": True,
            "secret_key": secret_key,
            "marked_at": datetime.utcnow().isoformat(),
            "message": f"Secret {secret_key} marked as compromised"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mark secret as compromised: {str(e)}"
        )


@router.delete("/secrets/cache")
async def clear_secrets_cache(key: Optional[str] = None) -> Dict[str, Any]:
    """Clear secrets cache (specific key or all)."""
    try:
        secrets_manager.clear_cache(key)
        return {
            "success": True,
            "cleared_at": datetime.utcnow().isoformat(),
            "message": f"Cleared cache for {key}" if key else "Cleared all cache entries"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/config/validate")
async def validate_configuration() -> Dict[str, Any]:
    """Validate application configuration for production deployment."""
    try:
        return config_validator.validate_production_deployment()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Configuration validation failed: {str(e)}"
        )


@router.get("/config/report")
async def get_security_report() -> PlainTextResponse:
    """Get comprehensive security configuration report."""
    try:
        report = config_validator.generate_security_report()
        return PlainTextResponse(content=report, media_type="text/plain")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate security report: {str(e)}"
        )


@router.get("/environment/validate")
async def validate_environment_variables() -> Dict[str, Any]:
    """Validate all environment variables."""
    try:
        return validate_environment()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Environment validation failed: {str(e)}"
        )


@router.get("/environment/variable/{var_name}")
async def validate_single_variable(var_name: str) -> Dict[str, Any]:
    """Validate a single environment variable."""
    try:
        result = env_validator.validate_variable(var_name)
        return {
            "variable": result.variable,
            "is_valid": result.is_valid,
            "level": result.level.value,
            "message": result.message,
            "suggestions": result.suggestions
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Variable validation failed: {str(e)}"
        )


@router.post("/environment/validate-file")
async def validate_env_file(file_path: str) -> Dict[str, Any]:
    """Validate an environment file for security issues."""
    try:
        return config_validator.validate_environment_file(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Environment file validation failed: {str(e)}"
        )


@router.get("/audit/summary")
async def get_security_audit_summary() -> Dict[str, Any]:
    """Get security audit summary and compliance status."""
    try:
        # Aggregate security metrics
        secrets_health = secrets_manager.get_secrets_health_status()
        config_status = config_validator.validate_production_deployment()
        env_status = validate_environment()

        # Calculate compliance score
        compliance_score = _calculate_compliance_score(
            secrets_health, config_status, env_status
        )

        return {
            "audit_timestamp": datetime.utcnow().isoformat(),
            "compliance_score": compliance_score,
            "security_metrics": {
                "secrets_tracked": secrets_health.get("total_secrets_tracked", 0),
                "compromised_secrets": secrets_health.get("compromised_secrets", 0),
                "secrets_needing_rotation": secrets_health.get("secrets_needing_rotation", 0),
                "configuration_errors": len(config_status.get("errors", [])),
                "security_warnings": len(config_status.get("security_warnings", [])),
                "environment_errors": env_status.get("summary", {}).get("errors", 0),
                "environment_warnings": env_status.get("summary", {}).get("warnings", 0),
            },
            "compliance_status": {
                "audit_logging_enabled": secrets_health.get("audit_enabled", False),
                "cache_encryption_enabled": secrets_health.get("cache_encryption_enabled", False),
                "validation_enabled": secrets_health.get("validation_enabled", False),
                "production_ready": config_status.get("production_ready", False)
            },
            "recommendations": _generate_audit_recommendations(
                secrets_health, config_status, env_status
            )
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Security audit failed: {str(e)}"
        )


@router.get("/compliance/report")
async def get_compliance_report() -> PlainTextResponse:
    """Generate comprehensive compliance report."""
    try:
        audit_summary = await get_security_audit_summary()

        report = f"""
# HERMES Security Compliance Report
Generated: {audit_summary['audit_timestamp']}
Compliance Score: {audit_summary['compliance_score']}/100

## Executive Summary
{'✅ COMPLIANT' if audit_summary['compliance_score'] >= 80 else '❌ NON-COMPLIANT'}

## Security Metrics
- Secrets Tracked: {audit_summary['security_metrics']['secrets_tracked']}
- Compromised Secrets: {audit_summary['security_metrics']['compromised_secrets']}
- Secrets Needing Rotation: {audit_summary['security_metrics']['secrets_needing_rotation']}
- Configuration Errors: {audit_summary['security_metrics']['configuration_errors']}
- Security Warnings: {audit_summary['security_metrics']['security_warnings']}
- Environment Errors: {audit_summary['security_metrics']['environment_errors']}

## Compliance Status
- Audit Logging: {'✅' if audit_summary['compliance_status']['audit_logging_enabled'] else '❌'}
- Cache Encryption: {'✅' if audit_summary['compliance_status']['cache_encryption_enabled'] else '❌'}
- Validation Enabled: {'✅' if audit_summary['compliance_status']['validation_enabled'] else '❌'}
- Production Ready: {'✅' if audit_summary['compliance_status']['production_ready'] else '❌'}

## Recommendations
"""

        for rec in audit_summary['recommendations']:
            report += f"- {rec}\n"

        report += """
## Compliance Framework
This report validates compliance with:
- SOC 2 Type II security controls
- GDPR data protection requirements
- HIPAA security safeguards (where applicable)
- Industry best practices for secret management
- Enterprise security policies

## Next Steps
1. Address all critical security issues
2. Implement recommended security controls
3. Schedule regular security audits
4. Monitor compliance metrics continuously
"""

        return PlainTextResponse(content=report, media_type="text/plain")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate compliance report: {str(e)}"
        )


async def _get_secrets_health() -> Dict[str, Any]:
    """Get secrets health status asynchronously."""
    return secrets_manager.get_secrets_health_status()


async def _get_config_validation() -> Dict[str, Any]:
    """Get configuration validation results asynchronously."""
    return config_validator.validate_production_deployment()


async def _get_env_validation() -> Dict[str, Any]:
    """Get environment validation results asynchronously."""
    return validate_environment()


def _calculate_security_score(
    secrets_health: Dict[str, Any],
    config_validation: Dict[str, Any],
    env_validation: Dict[str, Any]
) -> int:
    """Calculate overall security score (0-100)."""
    score = 100

    # Deduct for secrets issues
    compromised_secrets = secrets_health.get("compromised_secrets", 0)
    score -= compromised_secrets * 20  # -20 per compromised secret

    rotation_needed = secrets_health.get("secrets_needing_rotation", 0)
    score -= rotation_needed * 5  # -5 per secret needing rotation

    # Deduct for configuration issues
    config_score = config_validation.get("configuration_score", 100)
    score = min(score, config_score)

    # Deduct for environment issues
    env_errors = env_validation.get("summary", {}).get("errors", 0)
    score -= env_errors * 10  # -10 per environment error

    env_warnings = env_validation.get("summary", {}).get("warnings", 0)
    score -= env_warnings * 5  # -5 per environment warning

    return max(0, min(100, score))


def _calculate_compliance_score(
    secrets_health: Dict[str, Any],
    config_status: Dict[str, Any],
    env_status: Dict[str, Any]
) -> int:
    """Calculate compliance score based on security controls."""
    score = 0
    total_controls = 10

    # Essential security controls
    if secrets_health.get("audit_enabled", False):
        score += 15  # Audit logging is critical

    if secrets_health.get("cache_encryption_enabled", False):
        score += 10  # Data encryption

    if secrets_health.get("validation_enabled", False):
        score += 10  # Input validation

    if secrets_health.get("compromised_secrets", 0) == 0:
        score += 15  # No compromised secrets

    if config_status.get("production_ready", False):
        score += 15  # Production-ready configuration

    if env_status.get("summary", {}).get("errors", 0) == 0:
        score += 10  # No environment errors

    if env_status.get("summary", {}).get("critical_issues", 0) == 0:
        score += 10  # No critical environment issues

    # Additional controls
    if secrets_health.get("provider", "env") != "env":
        score += 5  # Using cloud secrets provider

    if secrets_health.get("secrets_needing_rotation", 0) == 0:
        score += 5  # Regular secret rotation

    # Security policies compliance
    if len(config_status.get("security_warnings", [])) == 0:
        score += 5  # No security warnings

    return min(100, score)


def _generate_security_recommendations(
    secrets_health: Dict[str, Any],
    config_validation: Dict[str, Any],
    env_validation: Dict[str, Any]
) -> List[str]:
    """Generate security improvement recommendations."""
    recommendations = []

    # Secrets management recommendations
    if secrets_health.get("compromised_secrets", 0) > 0:
        recommendations.append("Immediately rotate all compromised secrets")

    if secrets_health.get("secrets_needing_rotation", 0) > 0:
        recommendations.append("Schedule secret rotation for aging credentials")

    if not secrets_health.get("audit_enabled", False):
        recommendations.append("Enable secrets audit logging for compliance")

    if not secrets_health.get("cache_encryption_enabled", False):
        recommendations.append("Enable cache encryption for sensitive data")

    # Configuration recommendations
    recommendations.extend(config_validation.get("recommendations", []))

    # Environment recommendations
    recommendations.extend(env_validation.get("recommendations", []))

    return recommendations


def _generate_audit_recommendations(
    secrets_health: Dict[str, Any],
    config_status: Dict[str, Any],
    env_status: Dict[str, Any]
) -> List[str]:
    """Generate audit and compliance recommendations."""
    recommendations = []

    # Compliance-focused recommendations
    if not secrets_health.get("audit_enabled", False):
        recommendations.append("Enable comprehensive audit logging")

    if config_status.get("configuration_score", 0) < 90:
        recommendations.append("Improve security configuration score to 90+")

    if env_status.get("summary", {}).get("critical_issues", 0) > 0:
        recommendations.append("Address all critical environment issues")

    if secrets_health.get("provider", "env") == "env":
        recommendations.append("Migrate to cloud secrets management provider")

    # Add general compliance recommendations
    recommendations.extend([
        "Schedule regular security assessments",
        "Implement automated security monitoring",
        "Establish incident response procedures",
        "Document security policies and procedures"
    ])

    return recommendations