"""Clio OAuth 2.0 authentication handler."""

from __future__ import annotations

import base64
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from pydantic import BaseModel

from ...config import settings

logger = logging.getLogger(__name__)


class ClioTokens(BaseModel):
    """Clio OAuth tokens."""

    access_token: str
    refresh_token: str
    expires_at: datetime
    token_type: str = "Bearer"


class ClioAuthHandler:
    """Handles Clio OAuth 2.0 authentication flow."""

    # Clio OAuth endpoints
    AUTHORIZE_URL = "https://app.clio.com/oauth/authorize"
    TOKEN_URL = "https://app.clio.com/oauth/token"

    # Required scopes for HERMES integration
    SCOPES = [
        "read",
        "write",
        "contacts:read",
        "contacts:write",
        "matters:read",
        "matters:write",
        "activities:read",
        "activities:write",
        "time_entries:read",
        "time_entries:write",
        "documents:read",
        "documents:write",
        "calendar_entries:read",
        "calendar_entries:write",
    ]

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ):
        self.client_id = client_id or settings.clio_client_id
        self.client_secret = client_secret or settings.clio_client_secret
        self.redirect_uri = redirect_uri or settings.clio_redirect_uri

        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("Clio OAuth credentials not properly configured")

    def generate_authorization_url(self, tenant_id: str) -> tuple[str, str]:
        """Generate OAuth authorization URL and state parameter.

        Args:
            tenant_id: Tenant ID for security verification

        Returns:
            Tuple of (authorization_url, state)
        """
        state = self._generate_state(tenant_id)
        scopes = " ".join(self.SCOPES)

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scopes,
            "state": state,
            "access_type": "offline",  # Request refresh token
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        authorization_url = f"{self.AUTHORIZE_URL}?{query_string}"

        return authorization_url, state

    async def exchange_code_for_tokens(
        self, code: str, state: str, tenant_id: str
    ) -> ClioTokens:
        """Exchange authorization code for access tokens.

        Args:
            code: Authorization code from Clio
            state: State parameter for verification
            tenant_id: Tenant ID for verification

        Returns:
            ClioTokens object with access and refresh tokens

        Raises:
            ValueError: If state validation fails
            httpx.HTTPError: If token exchange fails
        """
        # Verify state parameter
        if not self._verify_state(state, tenant_id):
            raise ValueError("Invalid state parameter - possible CSRF attack")

        # Prepare token request
        auth_header = self._get_basic_auth_header()

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "HERMES-Legal-AI/1.0",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL, data=data, headers=headers, timeout=30.0
                )
                response.raise_for_status()

                token_data = response.json()

                # Calculate token expiry
                expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

                tokens = ClioTokens(
                    access_token=token_data["access_token"],
                    refresh_token=token_data["refresh_token"],
                    expires_at=expires_at,
                    token_type=token_data.get("token_type", "Bearer"),
                )

                logger.info(f"Successfully obtained Clio tokens for tenant {tenant_id}")
                return tokens

        except httpx.HTTPError as e:
            logger.error(f"Failed to exchange code for tokens: {e}")
            raise

    async def refresh_access_token(self, refresh_token: str) -> ClioTokens:
        """Refresh expired access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New ClioTokens object

        Raises:
            httpx.HTTPError: If refresh fails
        """
        auth_header = self._get_basic_auth_header()

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "HERMES-Legal-AI/1.0",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL, data=data, headers=headers, timeout=30.0
                )
                response.raise_for_status()

                token_data = response.json()

                # Calculate token expiry
                expires_in = token_data.get("expires_in", 3600)
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

                tokens = ClioTokens(
                    access_token=token_data["access_token"],
                    refresh_token=token_data.get("refresh_token", refresh_token),
                    expires_at=expires_at,
                    token_type=token_data.get("token_type", "Bearer"),
                )

                logger.info("Successfully refreshed Clio access token")
                return tokens

        except httpx.HTTPError as e:
            logger.error(f"Failed to refresh access token: {e}")
            raise

    async def revoke_token(self, token: str, token_type: str = "refresh_token") -> bool:
        """Revoke access or refresh token.

        Args:
            token: Token to revoke
            token_type: Type of token ("access_token" or "refresh_token")

        Returns:
            True if successful, False otherwise
        """
        auth_header = self._get_basic_auth_header()

        data = {
            "token": token,
            "token_type_hint": token_type,
        }

        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "HERMES-Legal-AI/1.0",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://app.clio.com/oauth/revoke",
                    data=data,
                    headers=headers,
                    timeout=30.0,
                )

                # OAuth revocation endpoint may return 200 even for invalid tokens
                success = response.status_code == 200

                if success:
                    logger.info(f"Successfully revoked Clio {token_type}")
                else:
                    logger.warning(
                        f"Failed to revoke Clio {token_type}: {response.status_code}"
                    )

                return success

        except httpx.HTTPError as e:
            logger.error(f"Error revoking token: {e}")
            return False

    def is_token_expired(self, tokens: ClioTokens) -> bool:
        """Check if access token is expired.

        Args:
            tokens: ClioTokens to check

        Returns:
            True if expired, False otherwise
        """
        # Add 5 minute buffer to prevent edge cases
        buffer = timedelta(minutes=5)
        return datetime.now(timezone.utc) + buffer >= tokens.expires_at

    def _generate_state(self, tenant_id: str) -> str:
        """Generate secure state parameter for OAuth.

        Args:
            tenant_id: Tenant ID to include in state

        Returns:
            Base64-encoded state parameter
        """
        # Create state with random value and tenant ID
        random_value = secrets.token_urlsafe(32)
        timestamp = int(datetime.now(timezone.utc).timestamp())

        state_data = f"{tenant_id}:{timestamp}:{random_value}"
        return base64.urlsafe_b64encode(state_data.encode()).decode()

    def _verify_state(self, state: str, tenant_id: str) -> bool:
        """Verify state parameter matches tenant.

        Args:
            state: State parameter to verify
            tenant_id: Expected tenant ID

        Returns:
            True if valid, False otherwise
        """
        try:
            decoded = base64.urlsafe_b64decode(state.encode()).decode()
            parts = decoded.split(":")

            if len(parts) != 3:
                return False

            state_tenant_id, timestamp_str, _ = parts

            # Check tenant ID matches
            if state_tenant_id != tenant_id:
                return False

            # Check timestamp isn't too old (1 hour max)
            timestamp = int(timestamp_str)
            current_timestamp = int(datetime.now(timezone.utc).timestamp())

            if current_timestamp - timestamp > 3600:  # 1 hour
                return False

            return True

        except Exception as e:
            logger.error(f"Error verifying state: {e}")
            return False


def _get_basic_auth_header(self) -> str:
    """Generate HTTP Basic Auth header for client authentication.

    Returns:
        Basic auth header value
    """
    credentials = f"{self.client_id}:{self.client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded_credentials}"


# Backward-compatible alias used by API endpoints
ClioAuthManager = ClioAuthHandler
