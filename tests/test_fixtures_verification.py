"""
Verification tests for conftest.py fixtures

These tests verify that all fixtures in conftest.py are working correctly.
Run with: pytest tests/test_fixtures_verification.py -v
"""

import pytest
from pathlib import Path


@pytest.mark.unit
class TestDatabaseFixtures:
    """Verify database fixtures work correctly."""

    async def test_db_session_fixture(self, db_session):
        """Test that db_session fixture provides valid session."""
        assert db_session is not None
        # Session should be async
        from sqlalchemy.ext.asyncio import AsyncSession
        assert isinstance(db_session, AsyncSession)

    async def test_test_engine_fixture(self, test_engine):
        """Test that test_engine fixture provides valid engine."""
        assert test_engine is not None


@pytest.mark.unit
class TestRedisFixtures:
    """Verify Redis fixtures work correctly."""

    async def test_redis_client_fixture(self, redis_client):
        """Test that redis_client fixture provides valid client."""
        assert redis_client is not None
        # Should be able to call set/get methods
        assert hasattr(redis_client, 'set')
        assert hasattr(redis_client, 'get')


@pytest.mark.unit
class TestAPIClientFixtures:
    """Verify API client fixtures work correctly."""

    def test_api_client_fixture(self, api_client):
        """Test that api_client fixture provides valid client."""
        assert api_client is not None
        from fastapi.testclient import TestClient
        assert isinstance(api_client, TestClient)

    async def test_async_api_client_fixture(self, async_api_client):
        """Test that async_api_client fixture provides valid client."""
        assert async_api_client is not None
        # Should be able to make requests
        assert hasattr(async_api_client, 'get')
        assert hasattr(async_api_client, 'post')


@pytest.mark.unit
class TestAuthenticationFixtures:
    """Verify authentication fixtures work correctly."""

    def test_mock_user_fixture(self, mock_user):
        """Test that mock_user fixture provides valid user data."""
        assert mock_user is not None
        assert mock_user["id"] == "test-user-123"
        assert mock_user["email"] == "test@lawfirm.com"
        assert "tenant_id" in mock_user
        assert "roles" in mock_user

    def test_mock_admin_user_fixture(self, mock_admin_user):
        """Test that mock_admin_user fixture provides valid admin data."""
        assert mock_admin_user is not None
        assert mock_admin_user["id"] == "admin-user-456"
        from hermes.auth.models import Role
        assert Role.ADMIN in mock_admin_user["roles"]

    def test_jwt_handler_fixture(self, jwt_handler):
        """Test that jwt_handler fixture provides valid handler."""
        assert jwt_handler is not None
        from hermes.auth.jwt_handler import JWTHandler
        assert isinstance(jwt_handler, JWTHandler)

    def test_auth_headers_fixture(self, auth_headers):
        """Test that auth_headers fixture provides valid headers."""
        assert auth_headers is not None
        assert "Authorization" in auth_headers
        assert auth_headers["Authorization"].startswith("Bearer ")

    def test_admin_auth_headers_fixture(self, admin_auth_headers):
        """Test that admin_auth_headers fixture provides valid headers."""
        assert admin_auth_headers is not None
        assert "Authorization" in admin_auth_headers
        assert admin_auth_headers["Authorization"].startswith("Bearer ")


@pytest.mark.unit
class TestMockServiceFixtures:
    """Verify mock service fixtures work correctly."""

    def test_mock_openai_client(self, mock_openai_client):
        """Test that mock_openai_client fixture works."""
        assert mock_openai_client is not None
        assert hasattr(mock_openai_client, 'chat')

    def test_mock_whisper_client(self, mock_whisper_client):
        """Test that mock_whisper_client fixture works."""
        assert mock_whisper_client is not None
        assert hasattr(mock_whisper_client, 'transcribe')

    def test_mock_kokoro_client(self, mock_kokoro_client):
        """Test that mock_kokoro_client fixture works."""
        assert mock_kokoro_client is not None
        assert hasattr(mock_kokoro_client, 'synthesize')

    def test_mock_clio_client(self, mock_clio_client):
        """Test that mock_clio_client fixture works."""
        assert mock_clio_client is not None
        assert hasattr(mock_clio_client, 'create_matter')

    def test_mock_stripe_client(self, mock_stripe_client):
        """Test that mock_stripe_client fixture works."""
        assert mock_stripe_client is not None
        assert hasattr(mock_stripe_client, 'checkout')

    def test_mock_lawpay_client(self, mock_lawpay_client):
        """Test that mock_lawpay_client fixture works."""
        assert mock_lawpay_client is not None
        assert hasattr(mock_lawpay_client, 'create_payment')

    def test_mock_zapier_client(self, mock_zapier_client):
        """Test that mock_zapier_client fixture works."""
        assert mock_zapier_client is not None
        assert hasattr(mock_zapier_client, 'send_webhook')


@pytest.mark.unit
class TestDataFixtures:
    """Verify test data fixtures work correctly."""

    def test_sample_audio_file(self, sample_audio_file):
        """Test that sample_audio_file fixture creates valid WAV file."""
        assert sample_audio_file is not None
        assert Path(sample_audio_file).exists()
        assert Path(sample_audio_file).suffix == ".wav"
        # Check file is not empty
        assert Path(sample_audio_file).stat().st_size > 0

    def test_sample_legal_matter(self, sample_legal_matter):
        """Test that sample_legal_matter fixture provides valid data."""
        assert sample_legal_matter is not None
        assert "client_name" in sample_legal_matter
        assert "matter_type" in sample_legal_matter
        assert sample_legal_matter["matter_type"] == "Personal Injury"

    def test_sample_client_intake(self, sample_client_intake):
        """Test that sample_client_intake fixture provides valid data."""
        assert sample_client_intake is not None
        assert "name" in sample_client_intake
        assert "email" in sample_client_intake
        assert "phone" in sample_client_intake

    def test_sample_conversation_transcript(self, sample_conversation_transcript):
        """Test that sample_conversation_transcript fixture provides valid data."""
        assert sample_conversation_transcript is not None
        assert isinstance(sample_conversation_transcript, str)
        assert "HERMES" in sample_conversation_transcript
        assert "CLIENT" in sample_conversation_transcript


@pytest.mark.unit
class TestConfigurationFixtures:
    """Verify configuration fixtures work correctly."""

    def test_test_settings(self, test_settings):
        """Test that test_settings fixture provides valid settings."""
        assert test_settings is not None
        from hermes.config import Settings
        assert isinstance(test_settings, Settings)

    def test_override_settings(self, override_settings, test_settings):
        """Test that override_settings fixture works."""
        assert override_settings is not None
        # Test overriding a setting
        original_value = test_settings.openai_model
        override_settings("openai_model", "test-model")
        assert test_settings.openai_model == "test-model"
