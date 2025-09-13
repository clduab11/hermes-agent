"""Persistence for Clio OAuth tokens (tenant/user scoped)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import settings
from .auth import ClioTokens

logger = logging.getLogger(__name__)


class TokenCipher:
    """Encrypts/decrypts tokens if a Fernet key is configured."""

    def __init__(self, key_b64: Optional[str]) -> None:
        self._fernet: Optional[Fernet] = None
        if key_b64:
            try:
                self._fernet = Fernet(key_b64)
            except Exception:
                logger.error(
                    "Invalid CLIO_TOKEN_ENCRYPTION_KEY; falling back to plaintext storage"
                )
                self._fernet = None

    def encrypt(self, value: str) -> str:
        if not self._fernet:
            return value
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str) -> str:
        if not self._fernet:
            return value
        try:
            return self._fernet.decrypt(value.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            # Stored as plaintext previously
            return value


_cipher = TokenCipher(settings.clio_token_encryption_key)


async def upsert_clio_tokens(
    session: AsyncSession,
    tenant_id: str,
    user_id: Optional[str],
    tokens: ClioTokens,
) -> None:
    """Insert or update tokens for a tenant/user."""
    enc_access = _cipher.encrypt(tokens.access_token)
    enc_refresh = _cipher.encrypt(tokens.refresh_token)
    expires_at = tokens.expires_at

    query = text(
        """
        INSERT INTO clio_tokens (tenant_id, user_id, access_token, refresh_token, expires_at, token_type, created_at, updated_at)
        VALUES (:tenant_id, :user_id, :access_token, :refresh_token, :expires_at, :token_type, NOW(), NOW())
        ON CONFLICT (tenant_id, user_id)
        DO UPDATE SET 
            access_token = EXCLUDED.access_token,
            refresh_token = EXCLUDED.refresh_token,
            expires_at = EXCLUDED.expires_at,
            token_type = EXCLUDED.token_type,
            updated_at = NOW()
        """
    )

    await session.execute(
        query,
        {
            "tenant_id": tenant_id,
            "user_id": user_id or "anonymous",
            "access_token": enc_access,
            "refresh_token": enc_refresh,
            "expires_at": expires_at,
            "token_type": tokens.token_type,
        },
    )
    await session.commit()


async def get_clio_tokens(
    session: AsyncSession,
    tenant_id: str,
    user_id: Optional[str],
) -> Optional[ClioTokens]:
    """Fetch stored tokens for tenant/user; returns None if not found."""
    query = text(
        """
        SELECT access_token, refresh_token, expires_at, token_type
        FROM clio_tokens
        WHERE tenant_id = :tenant_id AND user_id = :user_id
        """
    )
    result = await session.execute(
        query,
        {
            "tenant_id": tenant_id,
            "user_id": user_id or "anonymous",
        },
    )
    row = result.one_or_none()
    if not row:
        return None
    access_token = _cipher.decrypt(
        row[0] if hasattr(row, "__iter__") else row.access_token
    )
    refresh_token = _cipher.decrypt(
        row[1] if hasattr(row, "__iter__") else row.refresh_token
    )
    expires_at = row[2] if hasattr(row, "__iter__") else row.expires_at
    token_type = row[3] if hasattr(row, "__iter__") else row.token_type
    return ClioTokens(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        token_type=(token_type or "Bearer"),
    )


async def delete_clio_tokens(
    session: AsyncSession, tenant_id: str, user_id: Optional[str]
) -> int:
    """Delete stored tokens; returns number of rows deleted."""
    query = text(
        """
        DELETE FROM clio_tokens WHERE tenant_id = :tenant_id AND user_id = :user_id
        """
    )
    result = await session.execute(
        query, {"tenant_id": tenant_id, "user_id": user_id or "anonymous"}
    )
    await session.commit()
    return result.rowcount or 0
