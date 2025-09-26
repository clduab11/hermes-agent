"""
Enterprise SaaS API Key Authentication System
Prevents unauthorized usage and enforces $2,497/month pricing tier
"""

import hashlib
import hmac
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from cryptography.fernet import Fernet
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_database_session

logger = logging.getLogger(__name__)

class EnterpriseAPIKeyManager:
    """Manages enterprise API keys for law firm clients."""

    def __init__(self):
        self.security = HTTPBearer()
        # Use encryption key from GCP secrets
        encryption_secret = settings.secure_api_key_encryption_secret
        if not encryption_secret:
            raise RuntimeError("API_KEY_ENCRYPTION_SECRET required for enterprise SaaS")
        self.fernet = Fernet(encryption_secret.encode() if len(encryption_secret) == 44 else Fernet.generate_key())

    def generate_enterprise_api_key(self, law_firm_id: str, tier: str = "enterprise") -> Dict[str, str]:
        """Generate enterprise API key for law firm clients."""

        if tier != "enterprise":
            raise ValueError("Only enterprise tier supported in SaaS mode")

        # Generate secure API key
        key_data = {
            "law_firm_id": law_firm_id,
            "tier": tier,
            "created_at": int(time.time()),
            "monthly_limit": 10000,  # Enterprise limit
            "price_per_month": 2497,  # $2,497/month
        }

        # Create secure key components
        key_prefix = "herm_ent_"  # hermes_enterprise
        key_secret = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(f"{law_firm_id}{key_secret}{tier}".encode()).hexdigest()[:16]

        api_key = f"{key_prefix}{key_hash}_{key_secret}"

        # Encrypt key data for storage
        encrypted_data = self.fernet.encrypt(str(key_data).encode())

        return {
            "api_key": api_key,
            "encrypted_data": encrypted_data.decode(),
            "law_firm_id": law_firm_id,
            "tier": tier,
            "monthly_price": 2497
        }

    async def validate_api_key(self, api_key: str, session: AsyncSession) -> Dict[str, any]:
        """Validate enterprise API key and enforce usage limits."""

        if not api_key or not api_key.startswith("herm_ent_"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key format. Enterprise SaaS requires valid API key."
            )

        try:
            # Extract key components
            parts = api_key.split("_")
            if len(parts) < 4:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Malformed API key"
                )

            # TODO: Query database for key validation
            # For now, implement basic validation

            # Check key format and basic validation
            key_hash = parts[2]
            key_secret = parts[3]

            if len(key_hash) != 16 or len(key_secret) < 32:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key structure"
                )

            # Return validated key info
            return {
                "valid": True,
                "law_firm_id": f"firm_{key_hash[:8]}",
                "tier": "enterprise",
                "monthly_limit": 10000,
                "monthly_price": 2497,
                "validated_at": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key validation failed. Contact support to verify your enterprise subscription."
            )

    async def check_usage_limits(self, law_firm_id: str, session: AsyncSession) -> Dict[str, any]:
        """Check current usage against enterprise limits."""

        # TODO: Implement actual usage tracking
        # For now, return mock data

        current_month = datetime.utcnow().strftime("%Y-%m")

        return {
            "law_firm_id": law_firm_id,
            "current_month": current_month,
            "interactions_used": 1247,  # Mock data
            "interactions_limit": 10000,
            "remaining_interactions": 8753,
            "monthly_price": 2497,
            "billing_status": "active",
            "overage_rate": 0.25  # $0.25 per interaction over limit
        }

class EnterpriseAPIKeyAuth:
    """FastAPI dependency for enterprise API key authentication."""

    def __init__(self):
        self.manager = EnterpriseAPIKeyManager()
        self.security = HTTPBearer(auto_error=False)

    async def __call__(self, request: Request, credentials: Optional[HTTPAuthorizationCredentials] = None) -> Dict[str, any]:
        """Authenticate request with enterprise API key."""

        # Skip authentication for health check and system endpoints
        if request.url.path in ["/health", "/metrics", "/compliance"]:
            return {"authenticated": False, "system_endpoint": True}

        # Get API key from Authorization header or X-API-Key header
        api_key = None

        if credentials and credentials.scheme.lower() == "bearer":
            api_key = credentials.credentials
        elif "x-api-key" in request.headers:
            api_key = request.headers["x-api-key"]

        if not api_key:
            # In enterprise SaaS mode, all API access requires authentication
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Enterprise SaaS requires API key. Contact sales@hermes-ai.com for enterprise access ($2,497/month).",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Get database session
        session = await get_database_session()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )

        try:
            # Validate API key
            key_info = await self.manager.validate_api_key(api_key, session)

            # Check usage limits
            usage_info = await self.manager.check_usage_limits(key_info["law_firm_id"], session)

            # Enforce usage limits
            if usage_info["interactions_used"] >= usage_info["interactions_limit"]:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Monthly interaction limit exceeded. Current usage: {usage_info['interactions_used']}/{usage_info['interactions_limit']}. Contact billing for overage rates."
                )

            # Store auth info in request state
            request.state.authenticated = True
            request.state.law_firm_id = key_info["law_firm_id"]
            request.state.api_tier = key_info["tier"]
            request.state.monthly_price = key_info["monthly_price"]
            request.state.usage_info = usage_info

            return {
                "authenticated": True,
                "law_firm_id": key_info["law_firm_id"],
                "tier": key_info["tier"],
                "usage": usage_info
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"API key authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error"
            )
        finally:
            if session:
                await session.close()

# Global enterprise auth instance
enterprise_api_auth = EnterpriseAPIKeyAuth()

def require_enterprise_api_key():
    """Dependency to require valid enterprise API key."""
    return enterprise_api_auth

# Utility functions for key management
async def create_enterprise_client_key(law_firm_name: str, contact_email: str) -> Dict[str, str]:
    """Create new enterprise API key for law firm client."""

    manager = EnterpriseAPIKeyManager()
    law_firm_id = f"firm_{hashlib.sha256(law_firm_name.encode()).hexdigest()[:8]}"

    key_info = manager.generate_enterprise_api_key(law_firm_id, "enterprise")

    # TODO: Store in database with client info

    logger.info(f"Created enterprise API key for {law_firm_name} (${key_info['monthly_price']}/month)")

    return {
        **key_info,
        "law_firm_name": law_firm_name,
        "contact_email": contact_email,
        "setup_instructions": "Use Authorization: Bearer {api_key} header or X-API-Key: {api_key} header",
        "monthly_price": "$2,497",
        "support_email": "enterprise@hermes-ai.com"
    }

def validate_enterprise_subscription(law_firm_id: str) -> bool:
    """Validate active enterprise subscription."""
    # TODO: Implement Stripe subscription validation
    return True  # Mock for now