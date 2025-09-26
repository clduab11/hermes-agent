"""Secure secrets management for production environments."""

import json
import os
from typing import Any, Dict, Optional

import structlog

logger = structlog.get_logger()


class SecretsManager:
    """Manages secrets using environment variables with fallback to cloud providers."""

    def __init__(self):
        self.provider = os.getenv("SECRETS_PROVIDER", "env")
        self._cache: Dict[str, Any] = {}
        self._initialize_provider()

    def _initialize_provider(self):
        """Initialize the secrets provider."""
        if self.provider == "gcp":
            try:
                from google.cloud import secretmanager
                self.client = secretmanager.SecretManagerServiceClient()
                self.project_id = os.getenv("GCP_PROJECT_ID")
                logger.info("Initialized GCP Secret Manager")
            except ImportError:
                logger.warning("GCP Secret Manager not available, falling back to env")
                self.provider = "env"
        elif self.provider == "aws":
            try:
                import boto3
                self.client = boto3.client('secretsmanager')
                logger.info("Initialized AWS Secrets Manager")
            except ImportError:
                logger.warning("AWS Secrets Manager not available, falling back to env")
                self.provider = "env"

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve a secret value securely."""
        # Check cache first
        if key in self._cache:
            return self._cache[key]

        value = None

        if self.provider == "env":
            value = os.getenv(key, default)
        elif self.provider == "gcp":
            try:
                secret_name = f"projects/{self.project_id}/secrets/{key}/versions/latest"
                response = self.client.access_secret_version(request={"name": secret_name})
                value = response.payload.data.decode("UTF-8")
            except Exception as e:
                logger.error(f"Failed to retrieve secret from GCP: {e}")
                value = os.getenv(key, default)
        elif self.provider == "aws":
            try:
                response = self.client.get_secret_value(SecretId=key)
                value = response.get('SecretString')
                if not value and 'SecretBinary' in response:
                    value = response['SecretBinary'].decode("utf-8")
            except Exception as e:
                logger.error(f"Failed to retrieve secret from AWS: {e}")
                value = os.getenv(key, default)

        # Cache the value
        if value:
            self._cache[key] = value

        return value

    def get_json_secret(self, key: str, default: Optional[Dict] = None) -> Optional[Dict]:
        """Retrieve a JSON secret value."""
        value = self.get_secret(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON secret: {key}")
        return default

    def clear_cache(self):
        """Clear the secrets cache."""
        self._cache.clear()
        logger.info("Cleared secrets cache")


# Global instance
secrets_manager = SecretsManager()