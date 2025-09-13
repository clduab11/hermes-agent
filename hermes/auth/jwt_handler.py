"""JWT token generation and validation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable

import jwt

from ..config import settings
from .models import Role, TokenPair, TokenPayload


class JWTHandler:
    """Handles JWT encoding and decoding using RS256."""

    def __init__(
        self,
        private_key: str | None = None,
        public_key: str | None = None,
        algorithm: str | None = None,
        access_expire_minutes: int | None = None,
        refresh_expire_days: int | None = None,
    ) -> None:
        self.private_key = private_key or settings.jwt_private_key
        self.public_key = public_key or settings.jwt_public_key
        self.algorithm = algorithm or settings.jwt_algorithm
        self.access_expire_minutes = (
            access_expire_minutes or settings.access_token_expire_minutes
        )
        self.refresh_expire_days = (
            refresh_expire_days or settings.refresh_token_expire_days
        )

    def create_token_pair(
        self, subject: str, tenant_id: str, roles: Iterable[Role] | None = None
    ) -> TokenPair:
        """Create a new access/refresh token pair."""

        roles_list = list(roles or [])
        now = datetime.now(timezone.utc)
        iat = int(now.timestamp())
        access_payload = {
            "sub": subject,
            "tenant_id": tenant_id,
            "roles": roles_list,
            "type": "access",
            "exp": int(
                (now + timedelta(minutes=self.access_expire_minutes)).timestamp()
            ),
            "iat": iat,
        }
        refresh_payload = {
            "sub": subject,
            "tenant_id": tenant_id,
            "roles": roles_list,
            "type": "refresh",
            "exp": int((now + timedelta(days=self.refresh_expire_days)).timestamp()),
            "iat": iat,
        }
        access_token = jwt.encode(
            access_payload, self.private_key, algorithm=self.algorithm
        )
        refresh_token = jwt.encode(
            refresh_payload, self.private_key, algorithm=self.algorithm
        )
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    def refresh(self, refresh_token: str) -> TokenPair:
        """Generate a new token pair from a refresh token."""

        payload = self.decode(refresh_token)
        if payload.type != "refresh":
            raise ValueError("Token is not a refresh token")
        return self.create_token_pair(payload.sub, payload.tenant_id, payload.roles)

    def decode(self, token: str) -> TokenPayload:
        """Decode a JWT token and return a :class:`TokenPayload`."""

        payload = jwt.decode(token, self.public_key, algorithms=[self.algorithm])
        return TokenPayload(**payload)
