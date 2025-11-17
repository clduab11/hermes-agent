"""
Unit tests for JWT authentication middleware

Tests the JWTAuthMiddleware for request authentication and authorization.
Target coverage: 95%+ for auth.middleware module
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.testclient import TestClient

from hermes.auth.middleware import (
    JWTAuthMiddleware,
    get_current_user,
    require_permission
)
from hermes.auth.jwt_handler import JWTHandler
from hermes.auth.models import Role


@pytest.mark.unit
class TestJWTAuthMiddleware:
    """Test JWT authentication middleware"""

    def create_test_app(self, jwt_handler=None):
        """Helper to create test FastAPI app with middleware"""
        app = FastAPI()
        app.add_middleware(JWTAuthMiddleware, jwt_handler=jwt_handler)

        @app.get("/protected")
        async def protected_endpoint(request: Request):
            return {
                "tenant_id": request.state.tenant_id,
                "user_id": request.state.user_id,
                "roles": [str(r) for r in request.state.roles]
            }

        @app.get("/health")
        async def health_endpoint():
            return {"status": "healthy"}

        @app.post("/auth/login")
        async def login_endpoint():
            return {"message": "login"}

        return app

    def test_middleware_allows_health_endpoint_without_auth(self):
        """Should allow access to /health without authentication"""
        app = self.create_test_app()
        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_middleware_allows_auth_endpoints_without_auth(self):
        """Should allow access to /auth/* without authentication"""
        app = self.create_test_app()
        client = TestClient(app)

        response = client.post("/auth/login")
        assert response.status_code == 200
        assert response.json() == {"message": "login"}

    def test_middleware_rejects_request_without_auth_header(self):
        """Should reject requests without Authorization header"""
        app = self.create_test_app()
        client = TestClient(app)

        response = client.get("/protected")
        assert response.status_code == 401
        assert "Missing credentials" in response.json()["detail"]

    def test_middleware_rejects_request_with_invalid_auth_scheme(self):
        """Should reject requests with non-Bearer auth scheme"""
        app = self.create_test_app()
        client = TestClient(app)

        response = client.get("/protected", headers={"Authorization": "Basic invalid"})
        assert response.status_code == 401
        assert "Missing credentials" in response.json()["detail"]

    def test_middleware_rejects_request_with_malformed_header(self):
        """Should reject requests with malformed Authorization header"""
        app = self.create_test_app()
        client = TestClient(app)

        response = client.get("/protected", headers={"Authorization": "Bearer"})
        assert response.status_code == 401
        assert "Missing token" in response.json()["detail"]

    def test_middleware_accepts_valid_token(self, jwt_handler):
        """Should accept request with valid JWT token"""
        app = self.create_test_app(jwt_handler)
        client = TestClient(app)

        token_pair = jwt_handler.create_token_pair(
            subject="user123",
            tenant_id="tenant456",
            roles=[Role.ADMIN]
        )

        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token_pair.access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user123"
        assert data["tenant_id"] == "tenant456"
        assert "Role.ADMIN" in str(data["roles"])

    def test_middleware_rejects_expired_token(self, test_settings):
        """Should reject expired JWT token"""
        # Create handler with very short expiry
        handler = JWTHandler(
            private_key="test_key",
            public_key="test_key",
            algorithm="HS256",
            access_expire_minutes=-1  # Already expired
        )

        app = self.create_test_app(handler)
        client = TestClient(app)

        token_pair = handler.create_token_pair("user123", "tenant456")

        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token_pair.access_token}"}
        )

        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]

    def test_middleware_rejects_refresh_token_as_access_token(self, jwt_handler):
        """Should reject refresh token when access token is required"""
        app = self.create_test_app(jwt_handler)
        client = TestClient(app)

        token_pair = jwt_handler.create_token_pair("user123", "tenant456")

        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token_pair.refresh_token}"}
        )

        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]

    def test_middleware_rejects_tampered_token(self, jwt_handler):
        """Should reject token with tampered signature"""
        app = self.create_test_app(jwt_handler)
        client = TestClient(app)

        token_pair = jwt_handler.create_token_pair("user123", "tenant456")

        # Tamper with token
        parts = token_pair.access_token.split('.')
        parts[2] = "tampered_signature"
        tampered_token = '.'.join(parts)

        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {tampered_token}"}
        )

        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]

    def test_middleware_sets_request_state(self, jwt_handler):
        """Should set tenant_id, user_id, and roles in request state"""
        app = self.create_test_app(jwt_handler)
        client = TestClient(app)

        token_pair = jwt_handler.create_token_pair(
            subject="user123",
            tenant_id="tenant456",
            roles=[Role.ADMIN, Role.ATTORNEY]
        )

        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token_pair.access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == "tenant456"
        assert data["user_id"] == "user123"
        assert len(data["roles"]) == 2

    def test_middleware_handles_case_insensitive_bearer(self, jwt_handler):
        """Should handle case-insensitive 'Bearer' keyword"""
        app = self.create_test_app(jwt_handler)
        client = TestClient(app)

        token_pair = jwt_handler.create_token_pair("user123", "tenant456")

        # Test lowercase 'bearer'
        response = client.get(
            "/protected",
            headers={"Authorization": f"bearer {token_pair.access_token}"}
        )

        assert response.status_code == 200


@pytest.mark.unit
class TestGetCurrentUser:
    """Test get_current_user dependency"""

    @pytest.mark.asyncio
    async def test_get_current_user_with_valid_state(self):
        """Should return user dict from request state"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = "user123"
        request.state.tenant_id = "tenant456"
        request.state.roles = [Role.ADMIN]

        user = await get_current_user(request)

        assert user["id"] == "user123"
        assert user["tenant_id"] == "tenant456"
        assert Role.ADMIN.value in user["roles"]

    @pytest.mark.asyncio
    async def test_get_current_user_without_user_id_raises_error(self):
        """Should raise 401 when user_id not in request state"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = None

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Not authenticated" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_without_state_raises_error(self):
        """Should raise 401 when request has no state"""
        request = Mock(spec=Request)
        # No state attribute

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_current_user_infers_email_from_user_id(self):
        """Should infer email when user_id contains @"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = "user@example.com"
        request.state.tenant_id = "tenant456"
        request.state.roles = []

        user = await get_current_user(request)

        assert user["email"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_generates_email_for_non_email_user_id(self):
        """Should generate email when user_id doesn't contain @"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = "user123"
        request.state.tenant_id = "tenant456"
        request.state.roles = []

        user = await get_current_user(request)

        assert user["email"] == "user123@local"

    @pytest.mark.asyncio
    async def test_get_current_user_converts_role_enums_to_strings(self):
        """Should convert Role enums to string values"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = "user123"
        request.state.tenant_id = "tenant456"
        request.state.roles = [Role.ADMIN, Role.ATTORNEY]

        user = await get_current_user(request)

        assert "admin" in user["roles"]
        assert "attorney" in user["roles"]

    @pytest.mark.asyncio
    async def test_get_current_user_handles_string_roles(self):
        """Should handle roles that are already strings"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = "user123"
        request.state.tenant_id = "tenant456"
        request.state.roles = ["admin", "attorney"]  # Already strings

        user = await get_current_user(request)

        assert "admin" in user["roles"]
        assert "attorney" in user["roles"]

    @pytest.mark.asyncio
    async def test_get_current_user_handles_empty_roles(self):
        """Should handle empty roles list"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = "user123"
        request.state.tenant_id = "tenant456"
        request.state.roles = []

        user = await get_current_user(request)

        assert user["roles"] == []


@pytest.mark.unit
class TestRequirePermission:
    """Test require_permission dependency factory"""

    @pytest.mark.asyncio
    async def test_require_permission_allows_admin_for_analytics_read(self):
        """Should allow ADMIN role for analytics:read permission"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.roles = [Role.ADMIN]

        dependency = require_permission("analytics:read")
        result = await dependency(request)  # Should not raise

        assert result is None  # Permission granted

    @pytest.mark.asyncio
    async def test_require_permission_allows_attorney_for_analytics_read(self):
        """Should allow ATTORNEY role for analytics:read permission"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.roles = [Role.ATTORNEY]

        dependency = require_permission("analytics:read")
        result = await dependency(request)

        assert result is None

    @pytest.mark.asyncio
    async def test_require_permission_allows_staff_for_analytics_read(self):
        """Should allow STAFF role for analytics:read permission"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.roles = [Role.STAFF]

        dependency = require_permission("analytics:read")
        result = await dependency(request)

        assert result is None

    @pytest.mark.asyncio
    async def test_require_permission_denies_read_only_for_analytics_read(self):
        """Should deny READ_ONLY role for analytics:read permission"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.roles = [Role.READ_ONLY]

        dependency = require_permission("analytics:read")

        with pytest.raises(HTTPException) as exc_info:
            await dependency(request)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Insufficient permissions" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_permission_allows_only_admin_for_billing_manage(self):
        """Should allow only ADMIN for billing:manage permission"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.roles = [Role.ADMIN]

        dependency = require_permission("billing:manage")
        result = await dependency(request)

        assert result is None

    @pytest.mark.asyncio
    async def test_require_permission_denies_attorney_for_billing_manage(self):
        """Should deny ATTORNEY for billing:manage permission"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.roles = [Role.ATTORNEY]

        dependency = require_permission("billing:manage")

        with pytest.raises(HTTPException) as exc_info:
            await dependency(request)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_require_permission_allows_admin_and_attorney_for_clio_write(self):
        """Should allow ADMIN and ATTORNEY for clio:write permission"""
        # Test ADMIN
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.roles = [Role.ADMIN]

        dependency = require_permission("clio:write")
        await dependency(request)  # Should not raise

        # Test ATTORNEY
        request.state.roles = [Role.ATTORNEY]
        await dependency(request)  # Should not raise

    @pytest.mark.asyncio
    async def test_require_permission_denies_staff_for_clio_write(self):
        """Should deny STAFF for clio:write permission"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.roles = [Role.STAFF]

        dependency = require_permission("clio:write")

        with pytest.raises(HTTPException) as exc_info:
            await dependency(request)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_require_permission_defaults_to_admin_for_unknown_permission(self):
        """Should default to ADMIN-only for unknown permissions"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.roles = [Role.STAFF]

        dependency = require_permission("unknown:permission")

        with pytest.raises(HTTPException) as exc_info:
            await dependency(request)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_require_permission_allows_admin_for_unknown_permission(self):
        """Should allow ADMIN for unknown permissions"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.roles = [Role.ADMIN]

        dependency = require_permission("unknown:permission")
        result = await dependency(request)

        assert result is None

    @pytest.mark.asyncio
    async def test_require_permission_handles_string_roles(self):
        """Should handle roles as strings (not just enums)"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.roles = ["admin"]  # String instead of Role enum

        dependency = require_permission("billing:manage")
        result = await dependency(request)

        assert result is None

    @pytest.mark.asyncio
    async def test_require_permission_handles_mixed_role_types(self):
        """Should handle mix of Role enums and strings"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.roles = [Role.ADMIN, "attorney"]  # Mixed

        dependency = require_permission("clio:write")
        result = await dependency(request)

        assert result is None

    @pytest.mark.asyncio
    async def test_require_permission_handles_empty_roles(self):
        """Should deny access when roles list is empty"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.roles = []

        dependency = require_permission("analytics:read")

        with pytest.raises(HTTPException) as exc_info:
            await dependency(request)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_require_permission_handles_none_roles(self):
        """Should deny access when roles is None"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.roles = None

        dependency = require_permission("analytics:read")

        with pytest.raises(HTTPException) as exc_info:
            await dependency(request)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_require_permission_allows_with_multiple_roles(self):
        """Should grant access when user has multiple roles including required one"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.roles = [Role.READ_ONLY, Role.STAFF, Role.ATTORNEY]

        dependency = require_permission("analytics:read")
        result = await dependency(request)

        assert result is None  # Access granted due to STAFF role
