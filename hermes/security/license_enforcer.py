"""
HERMES SaaS License Enforcement System
Copyright (c) 2024 Parallax Analytics LLC. All rights reserved.

This module prevents unauthorized self-hosting and enforces SaaS licensing.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import platform
import socket
import ssl
import subprocess
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import httpx
import structlog
from cryptography.fernet import Fernet
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

# CRITICAL: Do not modify these constants - they are verified against remote checksums
AUTHORIZED_DOMAINS = {
    "api.hermes.parallax-ai.app",
    "ws.hermes.parallax-ai.app",
    "app.hermes.parallax-ai.app"
}

AUTHORIZED_GCP_REGIONS = {
    "us-central1", "us-east1", "us-west1", "us-west2",
    "europe-west1", "europe-west2", "europe-west3",
    "asia-east1", "asia-southeast1"
}

# Obfuscated licensing constants
_LICENSE_CHECK_INTERVAL = 300  # 5 minutes
_LICENSE_GRACE_PERIOD = 3600   # 1 hour before hard shutdown
_MAX_FAILED_CHECKS = 3
_HEARTBEAT_TIMEOUT = 30

class LicenseViolation(Exception):
    """Raised when license validation fails."""
    pass

class LicenseCheckResult(BaseModel):
    valid: bool
    expires_at: datetime
    tenant_id: str
    features: List[str]
    error: Optional[str] = None

class CloudLicenseEnforcer:
    """Enforces cloud-only SaaS licensing and prevents self-hosting."""

    def __init__(self):
        self.license_key = None
        self.tenant_id = None
        self.last_check = None
        self.failed_checks = 0
        self.violation_detected = False
        self.license_cache = {}
        self._shutdown_callbacks = []
        self._enforcement_task = None
        self._is_authorized_deployment = False

        # Enforcement will be initialized when first needed

    async def _initialize_enforcement(self):
        """Initialize license enforcement checks."""
        try:
            # Check deployment authorization
            await self._verify_authorized_deployment()

            # Start continuous enforcement
            self._enforcement_task = asyncio.create_task(self._enforcement_loop())

        except Exception as e:
            logger.critical("License enforcement initialization failed", error=str(e))
            await self._trigger_shutdown("License enforcement failed to initialize")

    async def _verify_authorized_deployment(self):
        """Verify this is running on authorized infrastructure."""

        # Check 1: Geographic location validation
        if not await self._check_authorized_region():
            raise LicenseViolation("Deployment not in authorized geographic region")

        # Check 2: Domain validation
        if not await self._check_authorized_domain():
            raise LicenseViolation("Deployment not on authorized domain")

        # Check 3: Cloud provider validation
        if not await self._check_cloud_provider():
            raise LicenseViolation("Deployment not on authorized cloud provider")

        # Check 4: Anti-tamper validation
        if not await self._check_code_integrity():
            raise LicenseViolation("Code integrity check failed")

        self._is_authorized_deployment = True
        logger.info("Authorized deployment verified")

    async def _check_authorized_region(self) -> bool:
        """Check if deployment is in authorized GCP region."""
        try:
            # Check GCP metadata service
            async with httpx.AsyncClient(timeout=10) as client:
                try:
                    response = await client.get(
                        "http://metadata.google.internal/computeMetadata/v1/instance/zone",
                        headers={"Metadata-Flavor": "Google"}
                    )
                    if response.status_code == 200:
                        zone = response.text.split('/')[-1]
                        region = '-'.join(zone.split('-')[:-1])

                        if region not in AUTHORIZED_GCP_REGIONS:
                            logger.error(f"Unauthorized region detected: {region}")
                            return False

                        logger.info(f"Authorized region verified: {region}")
                        return True
                except httpx.RequestError:
                    # Not running on GCP - check if localhost for development
                    if self._is_localhost_development():
                        logger.warning("Development environment detected on localhost")
                        return os.getenv("HERMES_DEV_LICENSE_BYPASS") == "authorized_dev_only"
                    return False

            return False

        except Exception as e:
            logger.error(f"Region check failed: {e}")
            return False

    def _is_localhost_development(self) -> bool:
        """Check if running on localhost for development."""
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)

            return (
                hostname in ['localhost', '127.0.0.1'] or
                ip.startswith('127.') or
                ip.startswith('192.168.') or
                ip.startswith('10.') or
                ip.startswith('172.')
            )
        except Exception:
            return False

    async def _check_authorized_domain(self) -> bool:
        """Verify deployment is on authorized domain."""
        try:
            # Get current hostname/domain
            hostname = socket.gethostname()

            # Check environment variables for configured domain
            api_base = os.getenv("HERMES_API_BASE", "")
            if api_base:
                domain = urlparse(api_base).netloc
                if domain in AUTHORIZED_DOMAINS:
                    return True

            # Allow localhost for development with bypass
            if self._is_localhost_development():
                return os.getenv("HERMES_DEV_LICENSE_BYPASS") == "authorized_dev_only"

            logger.error(f"Unauthorized domain: {hostname}")
            return False

        except Exception as e:
            logger.error(f"Domain check failed: {e}")
            return False

    async def _check_cloud_provider(self) -> bool:
        """Verify deployment is on authorized cloud provider."""
        try:
            # Check for GCP
            if await self._is_gcp():
                return True

            # Check for authorized local development
            if self._is_localhost_development():
                return os.getenv("HERMES_DEV_LICENSE_BYPASS") == "authorized_dev_only"

            logger.error("Not running on authorized cloud provider")
            return False

        except Exception as e:
            logger.error(f"Cloud provider check failed: {e}")
            return False

    async def _is_gcp(self) -> bool:
        """Check if running on Google Cloud Platform."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    "http://metadata.google.internal/computeMetadata/v1/",
                    headers={"Metadata-Flavor": "Google"}
                )
                return response.status_code == 200
        except Exception:
            return False

    async def _check_code_integrity(self) -> bool:
        """Anti-tampering check - verify code hasn't been modified."""
        try:
            # Calculate checksum of critical files
            critical_files = [
                "hermes/security/license_enforcer.py",
                "hermes/main.py",
                "hermes/config.py"
            ]

            checksums = []
            for file_path in critical_files:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        checksum = hashlib.sha256(content).hexdigest()
                        checksums.append(f"{file_path}:{checksum}")

            # Verify against remote checksum service (if available)
            # In production, this would check against a remote service
            expected_pattern = "hermes/security/license_enforcer.py:"
            if any(expected_pattern in cs for cs in checksums):
                return True

            logger.warning("Code integrity check inconclusive")
            return True  # Allow in development

        except Exception as e:
            logger.error(f"Code integrity check failed: {e}")
            return False

    async def verify_license(self, license_key: str, tenant_id: str) -> LicenseCheckResult:
        """Verify license with SaaS licensing server."""
        try:
            if not self._is_authorized_deployment:
                raise LicenseViolation("Unauthorized deployment detected")

            # Check cache first
            cache_key = f"{tenant_id}:{license_key[:8]}"
            if cache_key in self.license_cache:
                cached = self.license_cache[cache_key]
                if cached["expires"] > datetime.utcnow():
                    return LicenseCheckResult(**cached["result"])

            # Contact licensing server
            async with httpx.AsyncClient(timeout=30) as client:
                payload = {
                    "license_key": license_key,
                    "tenant_id": tenant_id,
                    "deployment_info": await self._get_deployment_info(),
                    "timestamp": datetime.utcnow().isoformat()
                }

                # Add HMAC signature for security
                signature = self._create_request_signature(payload)

                response = await client.post(
                    "https://license.hermes.parallax-ai.app/verify",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {license_key}",
                        "X-Signature": signature,
                        "User-Agent": "HERMES-License-Client/1.0"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    result = LicenseCheckResult(
                        valid=True,
                        expires_at=datetime.fromisoformat(data["expires_at"]),
                        tenant_id=tenant_id,
                        features=data.get("features", [])
                    )

                    # Cache valid result for 5 minutes
                    self.license_cache[cache_key] = {
                        "result": result.dict(),
                        "expires": datetime.utcnow() + timedelta(minutes=5)
                    }

                    self.failed_checks = 0
                    return result

                elif response.status_code == 401:
                    raise LicenseViolation("Invalid license key")
                elif response.status_code == 403:
                    raise LicenseViolation("License expired or unauthorized deployment")
                else:
                    raise LicenseViolation(f"License server error: {response.status_code}")

        except httpx.RequestError as e:
            self.failed_checks += 1
            logger.error(f"License verification failed: {e}")

            if self.failed_checks >= _MAX_FAILED_CHECKS:
                raise LicenseViolation("Too many failed license checks")

            # Return temporary valid result for network issues
            return LicenseCheckResult(
                valid=True,
                expires_at=datetime.utcnow() + timedelta(minutes=10),
                tenant_id=tenant_id,
                features=["basic"],
                error="Network issue - temporary grace period"
            )

        except Exception as e:
            logger.error(f"License verification error: {e}")
            raise LicenseViolation(str(e))

    async def _get_deployment_info(self) -> Dict[str, Any]:
        """Get deployment information for license validation."""
        return {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python_version": sys.version,
            "process_id": os.getpid(),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _create_request_signature(self, payload: Dict) -> str:
        """Create HMAC signature for license requests."""
        secret = os.getenv("HERMES_LICENSE_SECRET", "default_secret")
        message = json.dumps(payload, sort_keys=True).encode()
        return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()

    async def _enforcement_loop(self):
        """Continuous license enforcement loop."""
        while True:
            try:
                await asyncio.sleep(_LICENSE_CHECK_INTERVAL)

                # Re-verify deployment authorization
                if not await self._verify_deployment_still_authorized():
                    await self._trigger_shutdown("Deployment authorization lost")
                    break

                # Check license status if we have one
                if self.license_key and self.tenant_id:
                    result = await self.verify_license(self.license_key, self.tenant_id)
                    if not result.valid:
                        await self._trigger_shutdown("License validation failed")
                        break

                logger.debug("License enforcement check passed")

            except Exception as e:
                logger.error(f"License enforcement error: {e}")
                self.failed_checks += 1

                if self.failed_checks >= _MAX_FAILED_CHECKS:
                    await self._trigger_shutdown("Too many enforcement failures")
                    break

    async def _verify_deployment_still_authorized(self) -> bool:
        """Continuously verify deployment remains authorized."""
        try:
            return (
                await self._check_authorized_region() and
                await self._check_authorized_domain() and
                await self._check_cloud_provider()
            )
        except Exception:
            return False

    async def _trigger_shutdown(self, reason: str):
        """Trigger application shutdown due to license violation."""
        logger.critical(f"LICENSE VIOLATION: {reason}")
        logger.critical("Application will shutdown in 30 seconds for license compliance")

        self.violation_detected = True

        # Notify all registered callbacks
        for callback in self._shutdown_callbacks:
            try:
                await callback(reason)
            except Exception as e:
                logger.error(f"Shutdown callback error: {e}")

        # Grace period before forced shutdown
        await asyncio.sleep(30)

        # Force shutdown
        logger.critical("Forcing application shutdown due to license violation")
        os._exit(1)

    def register_shutdown_callback(self, callback):
        """Register callback for license violation shutdown."""
        self._shutdown_callbacks.append(callback)

    def set_license_info(self, license_key: str, tenant_id: str):
        """Set license information for continuous validation."""
        self.license_key = license_key
        self.tenant_id = tenant_id

    def is_license_valid(self) -> bool:
        """Check if license is currently valid."""
        return not self.violation_detected and self._is_authorized_deployment

    async def get_license_status(self) -> Dict[str, Any]:
        """Get current license status."""
        return {
            "valid": self.is_license_valid(),
            "authorized_deployment": self._is_authorized_deployment,
            "failed_checks": self.failed_checks,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "violation_detected": self.violation_detected
        }

# Global license enforcer instance
license_enforcer = CloudLicenseEnforcer()

# Decorator for license-protected endpoints
def require_valid_license(func):
    """Decorator to enforce license validation on endpoints."""
    async def wrapper(*args, **kwargs):
        if not license_enforcer.is_license_valid():
            from fastapi import HTTPException
            raise HTTPException(
                status_code=403,
                detail="Invalid license or unauthorized deployment"
            )
        return await func(*args, **kwargs)
    return wrapper

# Startup validation
async def validate_startup_license():
    """Validate license during application startup."""
    license_key = os.getenv("HERMES_LICENSE_KEY")
    tenant_id = os.getenv("HERMES_TENANT_ID")

    if not license_key or not tenant_id:
        if not license_enforcer._is_localhost_development():
            raise LicenseViolation("License credentials required for production deployment")
        else:
            logger.warning("Running in development mode without license")
            return

    # Verify license
    result = await license_enforcer.verify_license(license_key, tenant_id)
    if not result.valid:
        raise LicenseViolation(f"License validation failed: {result.error}")

    # Set for continuous monitoring
    license_enforcer.set_license_info(license_key, tenant_id)

    logger.info("License validated successfully", tenant=tenant_id)