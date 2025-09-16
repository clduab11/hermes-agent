"""
Test configuration security settings.

This module tests that the HERMES configuration follows security best practices,
particularly around API host binding defaults.
"""

import os
from unittest.mock import patch

import pytest

from hermes.config import Settings


class TestConfigSecurity:
    """Test security-related configuration settings."""

    def test_api_host_defaults_to_localhost(self):
        """Test that api_host defaults to localhost for security."""
        # Create a fresh settings instance to test defaults
        settings = Settings()
        
        # Verify the default is secure (localhost only)
        assert settings.api_host == "127.0.0.1"
        assert settings.api_host != "0.0.0.0"

    def test_api_host_can_be_overridden_via_env(self):
        """Test that api_host can be overridden via environment variables."""
        with patch.dict(os.environ, {"API_HOST": "0.0.0.0"}, clear=False):
            settings = Settings()
            # Should use environment variable value
            assert settings.api_host == "0.0.0.0"

    def test_api_host_container_compatibility(self):
        """Test container deployment compatibility via environment override."""
        # Test various container-friendly host values
        test_values = ["0.0.0.0", "10.0.0.1", "192.168.1.100"]
        
        for test_host in test_values:
            with patch.dict(os.environ, {"API_HOST": test_host}, clear=False):
                settings = Settings()
                assert settings.api_host == test_host

    def test_api_host_security_principle(self):
        """Test that the default follows the principle of least privilege."""
        settings = Settings()
        
        # Default should be localhost (principle of least privilege)
        assert settings.api_host in ["127.0.0.1", "localhost"]
        
        # Should not bind to all interfaces by default (security risk)
        assert settings.api_host != "0.0.0.0"

    def test_api_host_field_properties(self):
        """Test that the api_host field has correct properties."""
        settings = Settings()
        
        # Should be a string
        assert isinstance(settings.api_host, str)
        
        # Should have a description
        field_info = Settings.model_fields["api_host"]
        assert field_info.description == "API host address"
        
        # Should use secure default
        assert field_info.default == "127.0.0.1"

    def test_cors_origins_with_secure_host(self):
        """Test that CORS configuration works with secure host defaults."""
        # Test that CORS configuration still works properly with the new default
        settings = Settings(debug=False)
        
        # Should still work with localhost default
        assert settings.api_host == "127.0.0.1"
        
        # CORS configuration should be independent of host setting
        from hermes.config import get_cors_origins_list
        origins = get_cors_origins_list()
        assert isinstance(origins, list)
        assert len(origins) >= 1  # Should at least include GitHub Pages origin