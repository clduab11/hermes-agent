"""
Unit tests for JWT authentication

Tests the JWTHandler class for token creation, validation, and security.
Target coverage: 95%+ for auth.jwt_handler module
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import jwt as pyjwt

from hermes.auth.jwt_handler import JWTHandler
from hermes.auth.models import Role, TokenPair, TokenPayload


@pytest.mark.unit
class TestJWTCreation:
    """Test JWT token creation and encoding"""

    def test_create_token_pair(self, jwt_handler):
        """Should create valid access and refresh token pair"""
        token_pair = jwt_handler.create_token_pair(
            subject="user123",
            tenant_id="tenant456",
            roles=[Role.ADMIN]
        )

        assert token_pair is not None
        assert isinstance(token_pair, TokenPair)
        assert isinstance(token_pair.access_token, str)
        assert isinstance(token_pair.refresh_token, str)
        assert token_pair.token_type == "bearer"

    def test_access_token_contains_correct_claims(self, jwt_handler):
        """Should include all required claims in access token"""
        subject = "user123"
        tenant_id = "tenant456"
        roles = [Role.ADMIN, Role.ATTORNEY]

        token_pair = jwt_handler.create_token_pair(subject, tenant_id, roles)

        # Decode without verification to check claims
        payload = pyjwt.decode(
            token_pair.access_token,
            options={"verify_signature": False}
        )

        assert payload["sub"] == subject
        assert payload["tenant_id"] == tenant_id
        assert payload["roles"] == roles
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_refresh_token_contains_correct_claims(self, jwt_handler):
        """Should include all required claims in refresh token"""
        subject = "user123"
        tenant_id = "tenant456"
        roles = [Role.STAFF]

        token_pair = jwt_handler.create_token_pair(subject, tenant_id, roles)

        # Decode without verification to check claims
        payload = pyjwt.decode(
            token_pair.refresh_token,
            options={"verify_signature": False}
        )

        assert payload["sub"] == subject
        assert payload["tenant_id"] == tenant_id
        assert payload["roles"] == roles
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload

    def test_access_token_expiration_time(self, jwt_handler):
        """Should set correct expiration time for access token"""
        token_pair = jwt_handler.create_token_pair("user123", "tenant456")

        payload = pyjwt.decode(
            token_pair.access_token,
            options={"verify_signature": False}
        )

        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat_time = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)

        # Should expire in ~15 minutes (default access token expiry)
        time_diff = (exp_time - iat_time).total_seconds()
        expected_seconds = jwt_handler.access_expire_minutes * 60
        assert abs(time_diff - expected_seconds) < 5  # Allow 5 second tolerance

    def test_refresh_token_expiration_time(self, jwt_handler):
        """Should set correct expiration time for refresh token"""
        token_pair = jwt_handler.create_token_pair("user123", "tenant456")

        payload = pyjwt.decode(
            token_pair.refresh_token,
            options={"verify_signature": False}
        )

        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat_time = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)

        # Should expire in ~7 days (default refresh token expiry)
        time_diff = (exp_time - iat_time).total_seconds()
        expected_seconds = jwt_handler.refresh_expire_days * 24 * 60 * 60
        assert abs(time_diff - expected_seconds) < 5

    def test_create_token_with_no_roles(self, jwt_handler):
        """Should handle token creation with no roles"""
        token_pair = jwt_handler.create_token_pair(
            subject="user123",
            tenant_id="tenant456",
            roles=None
        )

        assert token_pair is not None
        payload = pyjwt.decode(
            token_pair.access_token,
            options={"verify_signature": False}
        )
        assert payload["roles"] == []

    def test_create_token_with_multiple_roles(self, jwt_handler):
        """Should handle multiple roles correctly"""
        roles = [Role.ADMIN, Role.ATTORNEY, Role.STAFF]
        token_pair = jwt_handler.create_token_pair(
            subject="user123",
            tenant_id="tenant456",
            roles=roles
        )

        payload = pyjwt.decode(
            token_pair.access_token,
            options={"verify_signature": False}
        )
        assert payload["roles"] == roles


@pytest.mark.unit
class TestJWTDecoding:
    """Test JWT token decoding and validation"""

    def test_decode_valid_access_token(self, jwt_handler):
        """Should successfully decode valid access token"""
        token_pair = jwt_handler.create_token_pair(
            subject="user123",
            tenant_id="tenant456",
            roles=[Role.ADMIN]
        )

        payload = jwt_handler.decode(token_pair.access_token)

        assert isinstance(payload, TokenPayload)
        assert payload.sub == "user123"
        assert payload.tenant_id == "tenant456"
        assert payload.type == "access"
        assert Role.ADMIN in payload.roles

    def test_decode_valid_refresh_token(self, jwt_handler):
        """Should successfully decode valid refresh token"""
        token_pair = jwt_handler.create_token_pair(
            subject="user123",
            tenant_id="tenant456",
            roles=[Role.STAFF]
        )

        payload = jwt_handler.decode(token_pair.refresh_token)

        assert isinstance(payload, TokenPayload)
        assert payload.sub == "user123"
        assert payload.type == "refresh"
        assert Role.STAFF in payload.roles

    def test_decode_expired_token_raises_error(self, test_settings):
        """Should raise error for expired token"""
        # Create handler with very short expiry
        handler = JWTHandler(
            private_key="test_key",
            public_key="test_key",
            algorithm="HS256",
            access_expire_minutes=-1  # Already expired
        )

        token_pair = handler.create_token_pair("user123", "tenant456")

        with pytest.raises(pyjwt.ExpiredSignatureError):
            handler.decode(token_pair.access_token)

    def test_decode_invalid_signature_raises_error(self, jwt_handler):
        """Should raise error for token with invalid signature"""
        token_pair = jwt_handler.create_token_pair("user123", "tenant456")

        # Tamper with token signature
        parts = token_pair.access_token.split('.')
        parts[2] = "invalid_signature"
        tampered_token = '.'.join(parts)

        with pytest.raises(pyjwt.InvalidSignatureError):
            jwt_handler.decode(tampered_token)

    def test_decode_malformed_token_raises_error(self, jwt_handler):
        """Should raise error for malformed token"""
        malformed_token = "not.a.valid.jwt.token"

        with pytest.raises(pyjwt.DecodeError):
            jwt_handler.decode(malformed_token)

    def test_decode_token_with_invalid_algorithm_raises_error(self, jwt_handler):
        """Should raise error for token with 'none' algorithm"""
        # Create token with 'none' algorithm (security vulnerability)
        payload = {
            "sub": "user123",
            "tenant_id": "tenant456",
            "roles": [],
            "type": "access",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp())
        }
        malicious_token = pyjwt.encode(payload, "", algorithm="none")

        with pytest.raises((pyjwt.DecodeError, pyjwt.InvalidAlgorithmError)):
            jwt_handler.decode(malicious_token)


@pytest.mark.unit
class TestJWTRefresh:
    """Test JWT token refresh functionality"""

    def test_refresh_with_valid_refresh_token(self, jwt_handler):
        """Should generate new token pair from valid refresh token"""
        original_pair = jwt_handler.create_token_pair(
            subject="user123",
            tenant_id="tenant456",
            roles=[Role.ADMIN]
        )

        new_pair = jwt_handler.refresh(original_pair.refresh_token)

        assert isinstance(new_pair, TokenPair)
        assert new_pair.access_token != original_pair.access_token
        assert new_pair.refresh_token != original_pair.refresh_token

        # Verify new tokens have same subject and roles
        new_payload = jwt_handler.decode(new_pair.access_token)
        assert new_payload.sub == "user123"
        assert new_payload.tenant_id == "tenant456"
        assert Role.ADMIN in new_payload.roles

    def test_refresh_with_access_token_raises_error(self, jwt_handler):
        """Should raise error when trying to refresh with access token"""
        token_pair = jwt_handler.create_token_pair("user123", "tenant456")

        with pytest.raises(ValueError, match="not a refresh token"):
            jwt_handler.refresh(token_pair.access_token)

    def test_refresh_preserves_all_claims(self, jwt_handler):
        """Should preserve all user claims when refreshing"""
        roles = [Role.ADMIN, Role.ATTORNEY]
        original_pair = jwt_handler.create_token_pair(
            subject="user123",
            tenant_id="tenant456",
            roles=roles
        )

        new_pair = jwt_handler.refresh(original_pair.refresh_token)
        new_payload = jwt_handler.decode(new_pair.access_token)

        assert new_payload.sub == "user123"
        assert new_payload.tenant_id == "tenant456"
        assert new_payload.roles == roles

    def test_refresh_updates_expiration_times(self, jwt_handler):
        """Should update expiration times when refreshing"""
        original_pair = jwt_handler.create_token_pair("user123", "tenant456")

        # Decode original tokens
        original_access_payload = pyjwt.decode(
            original_pair.access_token,
            options={"verify_signature": False}
        )

        # Wait a moment and refresh
        import time
        time.sleep(1)

        new_pair = jwt_handler.refresh(original_pair.refresh_token)
        new_access_payload = pyjwt.decode(
            new_pair.access_token,
            options={"verify_signature": False}
        )

        # New token should have later expiration
        assert new_access_payload["exp"] > original_access_payload["exp"]
        assert new_access_payload["iat"] > original_access_payload["iat"]


@pytest.mark.unit
@pytest.mark.security
class TestJWTSecurity:
    """Test JWT security features and edge cases"""

    def test_tokens_are_different_each_time(self, jwt_handler):
        """Should generate different tokens for same input (due to iat)"""
        import time

        pair1 = jwt_handler.create_token_pair("user123", "tenant456")
        time.sleep(1)  # Ensure different iat timestamp
        pair2 = jwt_handler.create_token_pair("user123", "tenant456")

        assert pair1.access_token != pair2.access_token
        assert pair1.refresh_token != pair2.refresh_token

    def test_different_subjects_produce_different_tokens(self, jwt_handler):
        """Should produce different tokens for different subjects"""
        pair1 = jwt_handler.create_token_pair("user1", "tenant1")
        pair2 = jwt_handler.create_token_pair("user2", "tenant1")

        assert pair1.access_token != pair2.access_token
        assert pair1.refresh_token != pair2.refresh_token

    def test_different_tenants_produce_different_tokens(self, jwt_handler):
        """Should produce different tokens for different tenants"""
        pair1 = jwt_handler.create_token_pair("user1", "tenant1")
        pair2 = jwt_handler.create_token_pair("user1", "tenant2")

        assert pair1.access_token != pair2.access_token
        assert pair1.refresh_token != pair2.refresh_token

    def test_cannot_decode_with_wrong_key(self):
        """Should fail to decode token with wrong key"""
        handler1 = JWTHandler(
            private_key="key1",
            public_key="key1",
            algorithm="HS256"
        )
        handler2 = JWTHandler(
            private_key="key2",
            public_key="key2",
            algorithm="HS256"
        )

        pair = handler1.create_token_pair("user123", "tenant456")

        with pytest.raises(pyjwt.InvalidSignatureError):
            handler2.decode(pair.access_token)

    def test_token_type_is_enforced(self, jwt_handler):
        """Should enforce token type in refresh operation"""
        token_pair = jwt_handler.create_token_pair("user123", "tenant456")

        # Access token should fail refresh
        with pytest.raises(ValueError):
            jwt_handler.refresh(token_pair.access_token)

        # Refresh token should succeed
        new_pair = jwt_handler.refresh(token_pair.refresh_token)
        assert new_pair is not None

    def test_custom_algorithm_initialization(self):
        """Should allow custom algorithm during initialization"""
        handler = JWTHandler(
            private_key="test_key",
            public_key="test_key",
            algorithm="HS512"
        )

        assert handler.algorithm == "HS512"

        pair = handler.create_token_pair("user123", "tenant456")
        payload = handler.decode(pair.access_token)
        assert payload.sub == "user123"

    def test_custom_expiry_times_initialization(self):
        """Should allow custom expiry times during initialization"""
        handler = JWTHandler(
            private_key="test_key",
            public_key="test_key",
            algorithm="HS256",
            access_expire_minutes=60,
            refresh_expire_days=30
        )

        assert handler.access_expire_minutes == 60
        assert handler.refresh_expire_days == 30

        pair = handler.create_token_pair("user123", "tenant456")

        access_payload = pyjwt.decode(
            pair.access_token,
            options={"verify_signature": False}
        )

        exp_time = datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc)
        iat_time = datetime.fromtimestamp(access_payload["iat"], tz=timezone.utc)
        time_diff_minutes = (exp_time - iat_time).total_seconds() / 60

        assert abs(time_diff_minutes - 60) < 1  # 60 minutes with small tolerance


@pytest.mark.unit
class TestJWTEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_roles_list(self, jwt_handler):
        """Should handle empty roles list"""
        pair = jwt_handler.create_token_pair("user123", "tenant456", roles=[])
        payload = jwt_handler.decode(pair.access_token)
        assert payload.roles == []

    def test_special_characters_in_subject(self, jwt_handler):
        """Should handle special characters in subject"""
        special_subject = "user@example.com"
        pair = jwt_handler.create_token_pair(special_subject, "tenant456")
        payload = jwt_handler.decode(pair.access_token)
        assert payload.sub == special_subject

    def test_unicode_characters_in_tenant_id(self, jwt_handler):
        """Should handle unicode characters in tenant ID"""
        tenant_id = "tenant-テナント-456"
        pair = jwt_handler.create_token_pair("user123", tenant_id)
        payload = jwt_handler.decode(pair.access_token)
        assert payload.tenant_id == tenant_id

    def test_very_long_subject_string(self, jwt_handler):
        """Should handle very long subject strings"""
        long_subject = "user" * 1000  # 4000 characters
        pair = jwt_handler.create_token_pair(long_subject, "tenant456")
        payload = jwt_handler.decode(pair.access_token)
        assert payload.sub == long_subject

    def test_all_role_types(self, jwt_handler):
        """Should handle all available role types"""
        all_roles = [Role.ADMIN, Role.ATTORNEY, Role.STAFF, Role.READ_ONLY]
        pair = jwt_handler.create_token_pair("user123", "tenant456", roles=all_roles)
        payload = jwt_handler.decode(pair.access_token)
        assert payload.roles == all_roles
