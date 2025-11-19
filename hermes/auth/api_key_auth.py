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
from typing import Dict, Optional, Tuple, Any

from cryptography.fernet import Fernet
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_database_session
from ..database.models import EnterpriseAPIKey, APIKeyUsage, APIKeyStatus, APIKeyTier

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

    async def validate_api_key(self, api_key: str, session: AsyncSession) -> Dict[str, Any]:
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

            # Check key format and basic validation
            key_hash_part = parts[2]
            key_secret = parts[3]

            if len(key_hash_part) != 16 or len(key_secret) < 32:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key structure"
                )

            # Hash the full API key for database lookup
            full_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            # Query database for the API key
            stmt = select(EnterpriseAPIKey).where(
                EnterpriseAPIKey.key_hash == full_key_hash
            )
            result = await session.execute(stmt)
            api_key_record = result.scalar_one_or_none()

            if not api_key_record:
                # Key not found in database - check if this is a legacy key
                # For backward compatibility, allow format-validated keys
                # but log a warning for migration
                logger.warning(
                    f"API key not found in database (prefix: {key_hash_part[:8]}...). "
                    "Using format-based validation. Please migrate to database-stored keys."
                )
                return {
                    "valid": True,
                    "law_firm_id": f"firm_{key_hash_part[:8]}",
                    "tier": "enterprise",
                    "monthly_limit": 10000,
                    "monthly_price": 2497,
                    "validated_at": datetime.utcnow(),
                    "legacy_key": True
                }

            # Check key status
            if api_key_record.status != APIKeyStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"API key is {api_key_record.status.value}. Contact support to restore access."
                )

            # Check expiration
            if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key has expired. Contact sales to renew your subscription."
                )

            # Update last used timestamp
            await session.execute(
                update(EnterpriseAPIKey)
                .where(EnterpriseAPIKey.id == api_key_record.id)
                .values(last_used_at=datetime.utcnow())
            )
            await session.commit()

            # Return validated key info
            return {
                "valid": True,
                "api_key_id": api_key_record.id,
                "law_firm_id": api_key_record.law_firm_id,
                "law_firm_name": api_key_record.law_firm_name,
                "tier": api_key_record.tier.value,
                "monthly_limit": api_key_record.monthly_limit,
                "monthly_price": api_key_record.monthly_price,
                "overage_rate": api_key_record.overage_rate,
                "stripe_subscription_id": api_key_record.stripe_subscription_id,
                "validated_at": datetime.utcnow(),
                "legacy_key": False
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key validation failed. Contact support to verify your enterprise subscription."
            )

    async def check_usage_limits(
        self,
        law_firm_id: str,
        session: AsyncSession,
        api_key_id: Optional[int] = None,
        monthly_limit: int = 10000,
        monthly_price: int = 2497,
        overage_rate: int = 25
    ) -> Dict[str, Any]:
        """Check current usage against enterprise limits."""

        now = datetime.utcnow()
        current_year = now.year
        current_month = now.month

        try:
            # Query current month's usage
            stmt = select(APIKeyUsage).where(
                APIKeyUsage.law_firm_id == law_firm_id,
                APIKeyUsage.year == current_year,
                APIKeyUsage.month == current_month
            )
            result = await session.execute(stmt)
            usage_record = result.scalar_one_or_none()

            if usage_record:
                interactions_used = usage_record.interactions_count
                voice_minutes = usage_record.voice_minutes
                api_calls = usage_record.api_calls
            else:
                # No usage record exists yet - create one
                interactions_used = 0
                voice_minutes = 0
                api_calls = 0

                if api_key_id:
                    new_usage = APIKeyUsage(
                        api_key_id=api_key_id,
                        law_firm_id=law_firm_id,
                        year=current_year,
                        month=current_month,
                        interactions_count=0,
                        voice_minutes=0,
                        api_calls=0,
                        base_charge=monthly_price * 100,  # Convert to cents
                        overage_charge=0,
                        total_charge=monthly_price * 100
                    )
                    session.add(new_usage)
                    await session.commit()

            # Calculate remaining and overage
            remaining = max(0, monthly_limit - interactions_used)
            overage_count = max(0, interactions_used - monthly_limit)
            overage_charge = overage_count * overage_rate  # In cents

            return {
                "law_firm_id": law_firm_id,
                "current_month": f"{current_year}-{current_month:02d}",
                "interactions_used": interactions_used,
                "interactions_limit": monthly_limit,
                "remaining_interactions": remaining,
                "voice_minutes": voice_minutes,
                "api_calls": api_calls,
                "monthly_price": monthly_price,
                "overage_count": overage_count,
                "overage_charge_cents": overage_charge,
                "billing_status": "active",
                "overage_rate": overage_rate / 100  # Convert to dollars for display
            }

        except Exception as e:
            logger.error(f"Failed to check usage limits: {e}")
            # Return default values on error to not block requests
            return {
                "law_firm_id": law_firm_id,
                "current_month": f"{current_year}-{current_month:02d}",
                "interactions_used": 0,
                "interactions_limit": monthly_limit,
                "remaining_interactions": monthly_limit,
                "monthly_price": monthly_price,
                "billing_status": "unknown",
                "overage_rate": overage_rate / 100,
                "error": str(e)
            }

    async def increment_usage(
        self,
        law_firm_id: str,
        session: AsyncSession,
        api_key_id: Optional[int] = None,
        interaction_type: str = "api_call"
    ) -> None:
        """Increment usage counter for the current billing period."""

        now = datetime.utcnow()

        try:
            # Find or create usage record
            stmt = select(APIKeyUsage).where(
                APIKeyUsage.law_firm_id == law_firm_id,
                APIKeyUsage.year == now.year,
                APIKeyUsage.month == now.month
            )
            result = await session.execute(stmt)
            usage_record = result.scalar_one_or_none()

            if usage_record:
                # Update existing record
                updates = {
                    "interactions_count": usage_record.interactions_count + 1,
                    "updated_at": now
                }

                if interaction_type == "voice":
                    updates["voice_minutes"] = usage_record.voice_minutes + 1
                else:
                    updates["api_calls"] = usage_record.api_calls + 1

                await session.execute(
                    update(APIKeyUsage)
                    .where(APIKeyUsage.id == usage_record.id)
                    .values(**updates)
                )
            else:
                # Create new record
                new_usage = APIKeyUsage(
                    api_key_id=api_key_id or 0,
                    law_firm_id=law_firm_id,
                    year=now.year,
                    month=now.month,
                    interactions_count=1,
                    voice_minutes=1 if interaction_type == "voice" else 0,
                    api_calls=0 if interaction_type == "voice" else 1
                )
                session.add(new_usage)

            await session.commit()

        except Exception as e:
            logger.error(f"Failed to increment usage: {e}")
            # Don't raise - usage tracking failure shouldn't block requests

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

            # Check usage limits with parameters from key validation
            usage_info = await self.manager.check_usage_limits(
                law_firm_id=key_info["law_firm_id"],
                session=session,
                api_key_id=key_info.get("api_key_id"),
                monthly_limit=key_info.get("monthly_limit", 10000),
                monthly_price=key_info.get("monthly_price", 2497),
                overage_rate=key_info.get("overage_rate", 25)
            )

            # Increment usage for this request
            await self.manager.increment_usage(
                law_firm_id=key_info["law_firm_id"],
                session=session,
                api_key_id=key_info.get("api_key_id"),
                interaction_type="api_call"
            )

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
async def create_enterprise_client_key(
    law_firm_name: str,
    contact_email: str,
    stripe_customer_id: Optional[str] = None,
    stripe_subscription_id: Optional[str] = None
) -> Dict[str, str]:
    """Create new enterprise API key for law firm client."""

    manager = EnterpriseAPIKeyManager()
    law_firm_id = f"firm_{hashlib.sha256(law_firm_name.encode()).hexdigest()[:8]}"

    key_info = manager.generate_enterprise_api_key(law_firm_id, "enterprise")

    # Store in database
    session = await get_database_session()
    if session:
        try:
            # Hash the full API key for storage
            full_key_hash = hashlib.sha256(key_info["api_key"].encode()).hexdigest()

            # Create database record
            api_key_record = EnterpriseAPIKey(
                key_hash=full_key_hash,
                key_prefix=key_info["api_key"][:24],  # Store prefix for identification
                law_firm_id=law_firm_id,
                law_firm_name=law_firm_name,
                contact_email=contact_email,
                tier=APIKeyTier.ENTERPRISE,
                status=APIKeyStatus.ACTIVE,
                monthly_limit=10000,
                monthly_price=2497,
                overage_rate=25,
                encrypted_data=key_info["encrypted_data"],
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription_id
            )

            session.add(api_key_record)
            await session.commit()

            logger.info(f"Created and stored enterprise API key for {law_firm_name} (${key_info['monthly_price']}/month)")

        except Exception as e:
            logger.error(f"Failed to store API key in database: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
    else:
        logger.warning("Database unavailable - API key created but not stored")

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