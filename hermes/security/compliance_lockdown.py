"""
HERMES SaaS Compliance Lockdown System
Copyright (c) 2024 Parallax Analytics LLC. All rights reserved.

This module enforces legal compliance and prevents unauthorized deployment.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

import structlog

logger = structlog.get_logger(__name__)

# CRITICAL: Legal and licensing constants - DO NOT MODIFY
LEGAL_NOTICE = """
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                          HERMES AI VOICE AGENT SYSTEM                               ║
║                        PROPRIETARY SOFTWARE - SaaS ONLY                             ║
║                      Copyright (c) 2024 Parallax Analytics LLC                      ║
╠══════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                      ║
║  🚨 LEGAL NOTICE: UNAUTHORIZED DEPLOYMENT PROHIBITED 🚨                            ║
║                                                                                      ║
║  This software is exclusively licensed for deployment on Parallax Analytics'       ║
║  authorized cloud infrastructure. Self-hosting, copying, or redistributing         ║
║  this software is strictly prohibited and constitutes:                             ║
║                                                                                      ║
║  • COPYRIGHT INFRINGEMENT (17 U.S.C. § 501)                                       ║
║  • BREACH OF SOFTWARE LICENSE AGREEMENT                                            ║
║  • VIOLATION OF DIGITAL MILLENNIUM COPYRIGHT ACT (DMCA)                           ║
║  • POTENTIAL CRIMINAL COPYRIGHT VIOLATION (17 U.S.C. § 506)                       ║
║                                                                                      ║
║  AUTHORIZED DEPLOYMENT: https://hermes.parallax-ai.app                             ║
║  LEGAL INQUIRIES: legal@parallax-ai.app                                            ║
║  CEASE & DESIST: unauthorized-use@parallax-ai.app                                  ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""

UNAUTHORIZED_DEPLOYMENT_WARNING = """
⚠️ ⚠️ ⚠️  UNAUTHORIZED DEPLOYMENT DETECTED  ⚠️ ⚠️ ⚠️

This software is exclusively licensed for SaaS deployment on authorized
Parallax Analytics infrastructure. Your current deployment appears to be
unauthorized.

IMMEDIATE ACTION REQUIRED:
1. Cease operation of this software immediately
2. Contact legal@parallax-ai.app for proper licensing
3. Migrate to official SaaS platform: https://hermes.parallax-ai.app

LEGAL CONSEQUENCES OF CONTINUED USE:
• Federal copyright infringement claims
• Statutory damages up to $150,000 per work
• Attorney's fees and legal costs
• Potential criminal prosecution
• Permanent injunctive relief

This notice serves as formal demand to cease and desist all
unauthorized use of HERMES software.
"""

COMPLIANCE_REQUIREMENTS = {
    "GDPR": {
        "regulation": "General Data Protection Regulation (EU) 2016/679",
        "requirements": [
            "Data processing consent mechanisms",
            "Right to erasure implementation",
            "Data portability features",
            "Privacy by design architecture",
            "Data breach notification procedures"
        ],
        "saas_only": True,
        "reason": "GDPR compliance requires centralized data governance and certified infrastructure"
    },
    "CCPA": {
        "regulation": "California Consumer Privacy Act (CCPA)",
        "requirements": [
            "Consumer data rights implementation",
            "Opt-out mechanisms",
            "Data category disclosure",
            "Third-party data sharing controls",
            "Consumer request processing"
        ],
        "saas_only": True,
        "reason": "CCPA compliance requires certified data handling processes"
    },
    "HIPAA": {
        "regulation": "Health Insurance Portability and Accountability Act",
        "requirements": [
            "PHI encryption at rest and in transit",
            "Access controls and audit logging",
            "Business Associate Agreements",
            "Breach notification procedures",
            "Administrative safeguards"
        ],
        "saas_only": True,
        "reason": "HIPAA compliance requires BAA and certified infrastructure"
    },
    "SOC2": {
        "regulation": "SOC 2 Type II Compliance",
        "requirements": [
            "Security controls audit",
            "Availability monitoring",
            "Processing integrity verification",
            "Confidentiality protections",
            "Privacy controls implementation"
        ],
        "saas_only": True,
        "reason": "SOC 2 certification only available on managed SaaS platform"
    }
}

class ComplianceLockdown:
    """Enforces legal compliance and prevents unauthorized deployment."""

    def __init__(self):
        self.compliance_violations = []
        self.lockdown_triggered = False

    def display_legal_notice(self):
        """Display legal notice on startup."""
        print(LEGAL_NOTICE)
        logger.info("Legal notice displayed")

    def check_deployment_authorization(self) -> Dict[str, Any]:
        """Check if deployment is legally authorized."""

        violations = []
        warnings = []

        # Check 1: Verify SaaS platform deployment
        if not self._is_authorized_saas_deployment():
            violations.append("Unauthorized deployment - SaaS license required")
            self._trigger_compliance_lockdown("unauthorized_deployment")

        # Check 2: Verify compliance requirements
        compliance_status = self._check_compliance_requirements()
        if compliance_status["violations"]:
            violations.extend(compliance_status["violations"])

        # Check 3: Verify legal licensing
        license_status = self._check_legal_licensing()
        if not license_status["valid"]:
            violations.append("Invalid or missing legal license")

        result = {
            "authorized": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "compliance_status": compliance_status,
            "license_status": license_status,
            "timestamp": datetime.utcnow().isoformat()
        }

        if not result["authorized"]:
            self._log_legal_violation(result)

        return result

    def _is_authorized_saas_deployment(self) -> bool:
        """Check if this is an authorized SaaS deployment."""

        # Check for required SaaS environment variables
        required_saas_vars = [
            "HERMES_LICENSE_KEY",
            "HERMES_TENANT_ID",
            "GOOGLE_CLOUD_PROJECT"  # Must be on GCP
        ]

        for var in required_saas_vars:
            if not os.getenv(var):
                logger.warning(f"Missing required SaaS variable: {var}")
                return False

        # Check for prohibited self-hosting indicators
        prohibited_indicators = [
            "localhost" in os.getenv("DATABASE_URL", ""),
            "127.0.0.1" in os.getenv("REDIS_URL", ""),
            os.path.exists("/home"),  # Linux self-hosting
            os.path.exists("/Users"),  # Mac self-hosting
            "docker" in os.getenv("HOSTNAME", "").lower(),
            os.getenv("KUBERNETES_SERVICE_HOST") and not os.getenv("GOOGLE_CLOUD_PROJECT")
        ]

        if any(prohibited_indicators):
            logger.error("Self-hosting indicators detected")
            return False

        return True

    def _check_compliance_requirements(self) -> Dict[str, Any]:
        """Check compliance with legal regulations."""

        violations = []
        compliant_regulations = []

        for regulation, details in COMPLIANCE_REQUIREMENTS.items():
            if details["saas_only"]:
                if not self._is_authorized_saas_deployment():
                    violations.append(
                        f"{regulation} compliance requires SaaS deployment: {details['reason']}"
                    )
                else:
                    compliant_regulations.append(regulation)

        return {
            "violations": violations,
            "compliant_regulations": compliant_regulations,
            "total_regulations": len(COMPLIANCE_REQUIREMENTS)
        }

    def _check_legal_licensing(self) -> Dict[str, Any]:
        """Check legal licensing status."""

        license_key = os.getenv("HERMES_LICENSE_KEY")
        tenant_id = os.getenv("HERMES_TENANT_ID")

        if not license_key or not tenant_id:
            return {
                "valid": False,
                "error": "Missing license credentials"
            }

        # Validate license format
        if not license_key.startswith("hl_"):
            return {
                "valid": False,
                "error": "Invalid license key format"
            }

        return {
            "valid": True,
            "license_type": "SaaS",
            "tenant_id": tenant_id[:8] + "***"  # Masked for security
        }

    def _trigger_compliance_lockdown(self, reason: str):
        """Trigger compliance lockdown."""

        if self.lockdown_triggered:
            return

        self.lockdown_triggered = True

        print(UNAUTHORIZED_DEPLOYMENT_WARNING)

        logger.critical(
            "COMPLIANCE LOCKDOWN TRIGGERED",
            reason=reason,
            timestamp=datetime.utcnow().isoformat()
        )

        # Log violation for legal action
        self._log_legal_violation({
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "system_info": self._get_system_info()
        })

        # Graceful shutdown
        print("\nShutting down for legal compliance...")
        print("Contact legal@parallax-ai.app for proper licensing.")

        sys.exit(1)

    def _log_legal_violation(self, violation_data: Dict[str, Any]):
        """Log legal violation for potential enforcement action."""

        try:
            violation_log = {
                "violation_type": "unauthorized_deployment",
                "timestamp": datetime.utcnow().isoformat(),
                "system_info": self._get_system_info(),
                "violation_data": violation_data
            }

            # Log to file for legal evidence
            log_file = "/tmp/hermes_legal_violation.log"
            try:
                with open(log_file, "a") as f:
                    import json
                    f.write(json.dumps(violation_log) + "\n")
            except Exception:
                pass  # Don't fail if can't write log

            logger.critical("Legal violation logged", violation=violation_log)

        except Exception as e:
            logger.error(f"Failed to log legal violation: {e}")

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for legal documentation."""

        import platform
        import socket

        try:
            return {
                "hostname": socket.gethostname(),
                "platform": platform.platform(),
                "python_version": sys.version,
                "environment_vars": {
                    key: "***" if "KEY" in key or "SECRET" in key or "TOKEN" in key else value
                    for key, value in os.environ.items()
                    if key.startswith(("HERMES_", "DATABASE_", "REDIS_"))
                }
            }
        except Exception:
            return {"error": "Could not gather system info"}

    def get_compliance_status(self) -> Dict[str, Any]:
        """Get current compliance status."""

        return {
            "compliant": not self.lockdown_triggered,
            "lockdown_triggered": self.lockdown_triggered,
            "violations": self.compliance_violations,
            "regulations": {
                name: {
                    "compliant": details["saas_only"] and self._is_authorized_saas_deployment(),
                    "requirements": details["requirements"],
                    "saas_only": details["saas_only"]
                }
                for name, details in COMPLIANCE_REQUIREMENTS.items()
            }
        }

    def get_legal_disclaimers(self) -> List[str]:
        """Get legal disclaimers for display."""

        return [
            "HERMES is proprietary software owned by Parallax Analytics LLC",
            "Unauthorized deployment, copying, or redistribution is prohibited",
            "This software is licensed exclusively for SaaS deployment",
            "Legal compliance requires use of official SaaS platform only",
            "Violation of license terms may result in legal action",
            "For proper licensing: legal@parallax-ai.app"
        ]

# Global compliance lockdown instance
compliance_lockdown = ComplianceLockdown()

def initialize_compliance_lockdown():
    """Initialize compliance lockdown on startup."""

    # Display legal notice
    compliance_lockdown.display_legal_notice()

    # Check deployment authorization
    auth_result = compliance_lockdown.check_deployment_authorization()

    if not auth_result["authorized"]:
        logger.critical("Compliance check failed", result=auth_result)
        # Lockdown will be triggered automatically
    else:
        logger.info("Compliance check passed - deployment authorized")

    return auth_result

def require_compliance_check():
    """Decorator to require compliance check on sensitive endpoints."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if compliance_lockdown.lockdown_triggered:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=451,  # Unavailable For Legal Reasons
                    detail="Service unavailable due to legal compliance requirements"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def get_legal_headers() -> Dict[str, str]:
    """Get legal headers for HTTP responses."""
    return {
        "X-Legal-Notice": "Proprietary-Software-SaaS-Only",
        "X-Copyright": "Copyright-2024-Parallax-Analytics-LLC",
        "X-License-Type": "SaaS-Exclusive",
        "X-Compliance-Status": "Authorized" if not compliance_lockdown.lockdown_triggered else "Violation"
    }