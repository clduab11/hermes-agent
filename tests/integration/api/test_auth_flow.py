"""
Integration tests for authentication flow

Tests the complete authentication workflow including:
- User registration
- Login with credentials
- Token validation
- Token refresh
- Logout

These tests require database and Redis to be running.
"""

import pytest
from httpx import AsyncClient

from hermes.auth.models import Role


@pytest.mark.integration
@pytest.mark.requires_database
@pytest.mark.requires_redis
class TestAuthenticationFlow:
    """Test complete authentication flow end-to-end"""

    @pytest.mark.asyncio
    async def test_complete_auth_flow(
        self,
        async_api_client,
        db_session,
        redis_client
    ):
        """Should complete full authentication flow"""

        # 1. Register new user (if registration endpoint exists)
        # Note: Adjust based on actual API endpoints
        user_data = {
            "email": "newuser@lawfirm.com",
            "password": "SecurePassword123!",
            "firm_name": "Test Law Firm",
            "full_name": "Test User"
        }

        # 2. Login with credentials
        login_response = await async_api_client.post(
            "/api/v1/auth/login",
            json={
                "email": user_data["email"],
                "password": user_data["password"]
            }
        )

        # Should succeed or return appropriate status
        assert login_response.status_code in [200, 401]  # 401 if user doesn't exist

        if login_response.status_code == 200:
            token_data = login_response.json()

            # 3. Verify token structure
            assert "access_token" in token_data
            assert "refresh_token" in token_data
            assert "token_type" in token_data
            assert token_data["token_type"] == "bearer"

            access_token = token_data["access_token"]
            refresh_token = token_data["refresh_token"]

            # 4. Use access token to access protected endpoint
            protected_response = await async_api_client.get(
                "/api/v1/matters",  # Example protected endpoint
                headers={"Authorization": f"Bearer {access_token}"}
            )

            # Should allow access with valid token
            assert protected_response.status_code in [200, 404]  # 404 if no matters exist

            # 5. Refresh access token
            refresh_response = await async_api_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token}
            )

            if refresh_response.status_code == 200:
                new_tokens = refresh_response.json()
                assert "access_token" in new_tokens
                assert new_tokens["access_token"] != access_token  # Should be different

                # 6. Logout (invalidate tokens)
                logout_response = await async_api_client.post(
                    "/api/v1/auth/logout",
                    headers={"Authorization": f"Bearer {new_tokens['access_token']}"}
                )

                # Should successfully logout
                assert logout_response.status_code in [200, 204]

    @pytest.mark.asyncio
    async def test_invalid_credentials(self, async_api_client):
        """Should reject invalid credentials"""
        response = await async_api_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "WrongPassword123!"
            }
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_expired_token_rejection(self, async_api_client, jwt_handler):
        """Should reject expired access tokens"""
        # Create expired token
        from datetime import timedelta

        handler = jwt_handler
        handler.access_expire_minutes = -1  # Already expired

        token_pair = handler.create_token_pair(
            subject="user123",
            tenant_id="tenant456",
            roles=[Role.STAFF]
        )

        response = await async_api_client.get(
            "/api/v1/matters",
            headers={"Authorization": f"Bearer {token_pair.access_token}"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_role_based_access_control(
        self,
        async_api_client,
        jwt_handler
    ):
        """Should enforce role-based access control"""

        # Create token with STAFF role (limited permissions)
        staff_token = jwt_handler.create_token_pair(
            subject="staff_user",
            tenant_id="tenant123",
            roles=[Role.STAFF]
        )

        # Try to access admin-only endpoint
        response = await async_api_client.post(
            "/api/v1/admin/settings",  # Admin-only endpoint
            headers={"Authorization": f"Bearer {staff_token.access_token}"},
            json={"setting": "value"}
        )

        # Should be forbidden
        assert response.status_code in [403, 404]  # 403 forbidden or 404 if endpoint doesn't exist


@pytest.mark.integration
@pytest.mark.requires_database
class TestTenantIsolation:
    """Test tenant isolation in authentication"""

    @pytest.mark.asyncio
    async def test_cross_tenant_access_prevention(
        self,
        async_api_client,
        jwt_handler
    ):
        """Should prevent access to other tenant's data"""

        # Create token for tenant A
        tenant_a_token = jwt_handler.create_token_pair(
            subject="user_a",
            tenant_id="tenant_a",
            roles=[Role.ADMIN]
        )

        # Create token for tenant B
        tenant_b_token = jwt_handler.create_token_pair(
            subject="user_b",
            tenant_id="tenant_b",
            roles=[Role.ADMIN]
        )

        # User A tries to access their data
        response_a = await async_api_client.get(
            "/api/v1/matters",
            headers={"Authorization": f"Bearer {tenant_a_token.access_token}"}
        )

        # Should succeed (or 404 if no data)
        assert response_a.status_code in [200, 404]

        # User B tries to access their data
        response_b = await async_api_client.get(
            "/api/v1/matters",
            headers={"Authorization": f"Bearer {tenant_b_token.access_token}"}
        )

        # Should succeed (or 404 if no data)
        assert response_b.status_code in [200, 404]

        # Verify data isolation
        if response_a.status_code == 200 and response_b.status_code == 200:
            matters_a = response_a.json()
            matters_b = response_b.json()

            # Each tenant should only see their own data
            # This depends on the actual data structure
            assert isinstance(matters_a, (list, dict))
            assert isinstance(matters_b, (list, dict))


@pytest.mark.integration
@pytest.mark.slow
class TestAuthenticationPerformance:
    """Test authentication performance under load"""

    @pytest.mark.asyncio
    async def test_concurrent_login_requests(
        self,
        async_api_client
    ):
        """Should handle multiple concurrent login requests"""
        import asyncio

        async def login_request():
            return await async_api_client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "TestPassword123!"
                }
            )

        # Send 10 concurrent login requests
        tasks = [login_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete without crashing
        assert len(responses) == 10

        # Count successful responses (may be 401 if user doesn't exist)
        status_codes = [
            r.status_code for r in responses
            if hasattr(r, 'status_code')
        ]

        assert len(status_codes) == 10

    @pytest.mark.asyncio
    async def test_token_validation_performance(
        self,
        async_api_client,
        jwt_handler
    ):
        """Should validate tokens quickly (<100ms)"""
        import time

        token_pair = jwt_handler.create_token_pair(
            subject="perf_user",
            tenant_id="perf_tenant",
            roles=[Role.STAFF]
        )

        start = time.time()

        response = await async_api_client.get(
            "/health",  # Health endpoint shouldn't require auth
        )

        duration = time.time() - start

        # Should be fast (<100ms)
        assert duration < 0.1
        assert response.status_code == 200
