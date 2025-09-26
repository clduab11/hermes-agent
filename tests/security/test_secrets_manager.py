"""Security tests for secrets manager functionality."""

import os
import pytest
from unittest.mock import Mock, patch

from hermes.security.secrets_manager import SecretsManager


def test_env_provider_initialization():
    """Test initialization with environment variable provider."""
    with patch.dict(os.environ, {"SECRETS_PROVIDER": "env"}):
        manager = SecretsManager()
        assert manager.provider == "env"


def test_get_secret_from_env():
    """Test retrieving secret from environment variables."""
    manager = SecretsManager()
    manager.provider = "env"

    with patch.dict(os.environ, {"TEST_SECRET": "test_value"}):
        secret = manager.get_secret("TEST_SECRET")
        assert secret == "test_value"


def test_get_secret_with_default():
    """Test retrieving secret with default value."""
    manager = SecretsManager()
    manager.provider = "env"

    secret = manager.get_secret("NONEXISTENT_SECRET", "default_value")
    assert secret == "default_value"


def test_get_secret_caching():
    """Test that secrets are cached properly."""
    manager = SecretsManager()
    manager.provider = "env"

    with patch.dict(os.environ, {"CACHED_SECRET": "cached_value"}):
        # First call
        secret1 = manager.get_secret("CACHED_SECRET")
        assert secret1 == "cached_value"
        assert "CACHED_SECRET" in manager._cache

        # Second call should use cache
        secret2 = manager.get_secret("CACHED_SECRET")
        assert secret2 == "cached_value"
        assert secret1 == secret2


def test_clear_cache():
    """Test cache clearing functionality."""
    manager = SecretsManager()
    manager._cache["test_key"] = "test_value"

    manager.clear_cache()
    assert len(manager._cache) == 0


def test_get_json_secret():
    """Test retrieving JSON secret."""
    manager = SecretsManager()
    manager.provider = "env"

    json_data = '{"key": "value", "number": 42}'
    with patch.dict(os.environ, {"JSON_SECRET": json_data}):
        secret = manager.get_json_secret("JSON_SECRET")
        assert secret == {"key": "value", "number": 42}


def test_get_json_secret_invalid_json():
    """Test handling of invalid JSON in secret."""
    manager = SecretsManager()
    manager.provider = "env"

    with patch.dict(os.environ, {"INVALID_JSON": "not json"}):
        secret = manager.get_json_secret("INVALID_JSON", {"default": "value"})
        assert secret == {"default": "value"}


@patch('hermes.security.secrets_manager.secretmanager')
def test_gcp_provider_initialization(mock_secretmanager):
    """Test GCP Secret Manager initialization."""
    with patch.dict(os.environ, {"SECRETS_PROVIDER": "gcp", "GCP_PROJECT_ID": "test-project"}):
        manager = SecretsManager()
        assert manager.provider == "gcp"
        assert hasattr(manager, 'client')
        assert manager.project_id == "test-project"


@patch('boto3.client')
def test_aws_provider_initialization(mock_boto_client):
    """Test AWS Secrets Manager initialization."""
    with patch.dict(os.environ, {"SECRETS_PROVIDER": "aws"}):
        manager = SecretsManager()
        assert manager.provider == "aws"
        assert hasattr(manager, 'client')


def test_fallback_to_env_provider():
    """Test fallback to env provider when cloud providers unavailable."""
    # Test GCP fallback
    with patch.dict(os.environ, {"SECRETS_PROVIDER": "gcp"}):
        with patch('hermes.security.secrets_manager.logger'):
            manager = SecretsManager()
            # Should fall back to env due to import error
            assert manager.provider == "env"

    # Test AWS fallback
    with patch.dict(os.environ, {"SECRETS_PROVIDER": "aws"}):
        with patch('hermes.security.secrets_manager.logger'):
            manager = SecretsManager()
            # Should fall back to env due to import error
            assert manager.provider == "env"


@pytest.fixture
def gcp_manager():
    """Create manager with mocked GCP client."""
    with patch('hermes.security.secrets_manager.secretmanager'):
        with patch.dict(os.environ, {"SECRETS_PROVIDER": "gcp", "GCP_PROJECT_ID": "test-project"}):
            manager = SecretsManager()
            manager.client = Mock()
            return manager


def test_gcp_secret_retrieval(gcp_manager):
    """Test secret retrieval from GCP Secret Manager."""
    # Mock successful response
    mock_response = Mock()
    mock_response.payload.data.decode.return_value = "gcp_secret_value"
    gcp_manager.client.access_secret_version.return_value = mock_response

    secret = gcp_manager.get_secret("TEST_SECRET")
    assert secret == "gcp_secret_value"

    # Verify correct secret path was used
    gcp_manager.client.access_secret_version.assert_called_once()
    call_args = gcp_manager.client.access_secret_version.call_args
    assert "projects/test-project/secrets/TEST_SECRET/versions/latest" in str(call_args)


def test_gcp_secret_fallback_to_env(gcp_manager):
    """Test fallback to env when GCP fails."""
    # Mock GCP failure
    gcp_manager.client.access_secret_version.side_effect = Exception("GCP Error")

    with patch.dict(os.environ, {"TEST_SECRET": "env_fallback_value"}):
        secret = gcp_manager.get_secret("TEST_SECRET")
        assert secret == "env_fallback_value"


@pytest.fixture
def aws_manager():
    """Create manager with mocked AWS client."""
    with patch('boto3.client'):
        with patch.dict(os.environ, {"SECRETS_PROVIDER": "aws"}):
            manager = SecretsManager()
            manager.client = Mock()
            return manager


def test_aws_secret_retrieval(aws_manager):
    """Test secret retrieval from AWS Secrets Manager."""
    # Mock successful response
    aws_manager.client.get_secret_value.return_value = {"SecretString": "aws_secret_value"}

    secret = aws_manager.get_secret("TEST_SECRET")
    assert secret == "aws_secret_value"

    aws_manager.client.get_secret_value.assert_called_once_with(SecretId="TEST_SECRET")


def test_aws_secret_binary_retrieval(aws_manager):
    """Test binary secret retrieval from AWS Secrets Manager."""
    # Mock binary response
    aws_manager.client.get_secret_value.return_value = {
        "SecretBinary": b"binary_secret_value"
    }

    secret = aws_manager.get_secret("TEST_SECRET")
    assert secret == "binary_secret_value"


def test_aws_secret_fallback_to_env(aws_manager):
    """Test fallback to env when AWS fails."""
    # Mock AWS failure
    aws_manager.client.get_secret_value.side_effect = Exception("AWS Error")

    with patch.dict(os.environ, {"TEST_SECRET": "env_fallback_value"}):
        secret = aws_manager.get_secret("TEST_SECRET")
        assert secret == "env_fallback_value"