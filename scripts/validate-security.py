#!/usr/bin/env python3
"""
Security validation script for HERMES production deployment.

This script performs comprehensive security checks before deployment:
- Secrets management validation
- Configuration security assessment
- Environment variable validation
- Compliance checking
- Security report generation

Usage:
    python scripts/validate-security.py [--report-file security-report.txt] [--fail-on-warnings]
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from hermes.security.secrets_manager import secrets_manager, validate_production_secrets
from hermes.security.config_validator import config_validator
from hermes.security.env_validator import env_validator, validate_environment


def main():
    parser = argparse.ArgumentParser(description='Validate HERMES security configuration')
    parser.add_argument('--report-file', help='Output security report to file')
    parser.add_argument('--fail-on-warnings', action='store_true',
                        help='Fail validation if security warnings are found')
    parser.add_argument('--env-file', help='Validate specific environment file')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()

    print("🔒 HERMES Security Validation")
    print("=" * 50)

    # Track overall status
    has_errors = False
    has_warnings = False

    # 1. Validate secrets management
    print("\n📋 Validating Secrets Management...")
    secrets_validation = validate_production_secrets()

    if secrets_validation["ready"]:
        print("✅ Secrets validation: PASSED")
    else:
        print("❌ Secrets validation: FAILED")
        has_errors = True

        if secrets_validation["missing_secrets"]:
            print(f"   Missing secrets: {', '.join(secrets_validation['missing_secrets'])}")

        for invalid_secret in secrets_validation["invalid_secrets"]:
            print(f"   Invalid secret {invalid_secret['key']}: {invalid_secret['error']}")

    if secrets_validation["warnings"]:
        print(f"⚠️  Secrets warnings: {len(secrets_validation['warnings'])}")
        for warning in secrets_validation["warnings"]:
            print(f"   {warning}")
        has_warnings = True

    # 2. Validate configuration
    print("\n🔧 Validating Configuration...")
    config_validation = config_validator.validate_production_deployment()

    if config_validation["production_ready"]:
        print("✅ Configuration validation: PASSED")
        print(f"   Security score: {config_validation['configuration_score']}/100")
    else:
        print("❌ Configuration validation: FAILED")
        has_errors = True

    if config_validation["errors"]:
        print(f"   Configuration errors: {len(config_validation['errors'])}")
        for error in config_validation["errors"]:
            print(f"   - {error}")

    if config_validation["security_warnings"]:
        print(f"⚠️  Security warnings: {len(config_validation['security_warnings'])}")
        for warning in config_validation["security_warnings"]:
            print(f"   - {warning}")
        has_warnings = True

    # 3. Validate environment variables
    print("\n🌍 Validating Environment Variables...")
    env_validation = validate_environment()

    if env_validation["summary"]["production_ready"]:
        print("✅ Environment validation: PASSED")
    else:
        print("❌ Environment validation: FAILED")
        has_errors = True

    print(f"   Total variables checked: {env_validation['summary']['total_variables']}")
    print(f"   Valid variables: {env_validation['summary']['valid_variables']}")

    if env_validation["summary"]["errors"] > 0:
        print(f"   Errors: {env_validation['summary']['errors']}")

    if env_validation["summary"]["warnings"] > 0:
        print(f"   Warnings: {env_validation['summary']['warnings']}")
        has_warnings = True

    if env_validation["summary"]["critical_issues"] > 0:
        print(f"   Critical issues: {env_validation['summary']['critical_issues']}")
        has_errors = True

    # 4. Validate specific environment file if provided
    if args.env_file:
        print(f"\n📄 Validating Environment File: {args.env_file}")
        file_validation = config_validator.validate_environment_file(args.env_file)

        if "error" in file_validation:
            print(f"❌ File validation failed: {file_validation['error']}")
            has_errors = True
        else:
            if file_validation["is_safe"]:
                print("✅ Environment file validation: PASSED")
            else:
                print("❌ Environment file validation: FAILED")
                has_errors = True

                for issue in file_validation["issues"]:
                    print(f"   - {issue}")

            if file_validation["recommendations"]:
                print("💡 Recommendations:")
                for rec in file_validation["recommendations"]:
                    print(f"   - {rec}")

    # 5. Generate security report
    if args.report_file:
        print(f"\n📊 Generating Security Report: {args.report_file}")
        try:
            security_report = config_validator.generate_security_report()
            with open(args.report_file, 'w') as f:
                f.write(security_report)
            print(f"✅ Security report saved to: {args.report_file}")
        except Exception as e:
            print(f"❌ Failed to generate security report: {e}")
            has_errors = True

    # 6. Secrets health check
    print("\n🔐 Secrets Health Check...")
    secrets_health = secrets_manager.get_secrets_health_status()

    print(f"   Provider: {secrets_health['provider']}")
    print(f"   Tracked secrets: {secrets_health['total_secrets_tracked']}")
    print(f"   Cache encryption: {'✅' if secrets_health['cache_encryption_enabled'] else '❌'}")
    print(f"   Audit logging: {'✅' if secrets_health['audit_enabled'] else '❌'}")

    if secrets_health['compromised_secrets'] > 0:
        print(f"🚨 Compromised secrets detected: {secrets_health['compromised_secrets']}")
        has_errors = True

    if secrets_health['secrets_needing_rotation'] > 0:
        print(f"🔄 Secrets needing rotation: {secrets_health['secrets_needing_rotation']}")
        has_warnings = True

    # 7. Overall assessment
    print("\n" + "=" * 50)
    print("📋 SECURITY VALIDATION SUMMARY")
    print("=" * 50)

    # Overall status
    if has_errors:
        print("❌ OVERALL STATUS: FAILED - Critical issues detected")
        print("🚨 DO NOT DEPLOY - Address all errors before production deployment")
    elif has_warnings and args.fail_on_warnings:
        print("⚠️  OVERALL STATUS: FAILED - Security warnings present")
        print("🔒 Address security warnings before deployment")
    elif has_warnings:
        print("⚠️  OVERALL STATUS: PASSED WITH WARNINGS")
        print("💡 Consider addressing warnings for optimal security")
    else:
        print("✅ OVERALL STATUS: PASSED")
        print("🚀 Configuration is production-ready")

    # Environment-specific guidance
    environment = os.getenv("ENVIRONMENT", "development")
    print(f"\n🌍 Current Environment: {environment}")

    if environment == "production":
        print("🏢 Production deployment detected")
        if has_errors:
            print("🚫 PRODUCTION DEPLOYMENT BLOCKED")
        else:
            print("✅ Production deployment approved")
    else:
        print("🧪 Non-production environment")

    # Recommendations
    print("\n💡 NEXT STEPS:")
    if has_errors:
        print("1. Address all critical errors listed above")
        print("2. Re-run validation script")
        print("3. Review security policies and procedures")
    elif has_warnings:
        print("1. Review and address security warnings")
        print("2. Consider implementing recommended security controls")
        print("3. Schedule regular security assessments")
    else:
        print("1. Proceed with deployment")
        print("2. Monitor security metrics post-deployment")
        print("3. Schedule next security review")

    # Exit with appropriate code
    if has_errors:
        sys.exit(1)
    elif has_warnings and args.fail_on_warnings:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()