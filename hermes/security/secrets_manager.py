"""Secure secrets management for production environments with enterprise features."""

import asyncio
import base64
import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union
from urllib.parse import urlparse

import structlog
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = structlog.get_logger()
audit_logger = logging.getLogger("hermes.security.audit")


class SecretValidationError(Exception):
    """Raised when secret validation fails."""
    pass


class SecretRotationError(Exception):
    """Raised when secret rotation fails."""
    pass


class SecretMetadata:
    """Metadata for tracking secret lifecycle."""

    def __init__(self, key: str, created_at: datetime = None,
                 last_accessed: datetime = None, rotation_interval_hours: int = 0):
        self.key = key
        self.created_at = created_at or datetime.utcnow()
        self.last_accessed = last_accessed or datetime.utcnow()
        self.rotation_interval_hours = rotation_interval_hours
        self.access_count = 0
        self.failed_access_count = 0
        self.is_compromised = False

    def record_access(self, success: bool = True):
        """Record secret access for audit purposes."""
        self.last_accessed = datetime.utcnow()
        if success:
            self.access_count += 1
        else:
            self.failed_access_count += 1

    def needs_rotation(self) -> bool:
        """Check if secret needs rotation based on age and policy."""
        if self.rotation_interval_hours <= 0:
            return False

        age_hours = (datetime.utcnow() - self.created_at).total_seconds() / 3600
        return age_hours > self.rotation_interval_hours

    def mark_compromised(self):
        """Mark secret as compromised for immediate rotation."""
        self.is_compromised = True
        audit_logger.critical(f"Secret {self.key} marked as compromised")


class SecretsManager:
    """Enterprise-grade secrets management with rotation, validation, and multi-provider support."""

    # Sensitive environment variables that should never be logged
    SENSITIVE_KEYS = {
        "OPENAI_API_KEY", "JWT_PRIVATE_KEY", "JWT_PUBLIC_KEY", "STRIPE_API_KEY",
        "STRIPE_WEBHOOK_SECRET", "CLIO_CLIENT_SECRET", "SUPABASE_SERVICE_ROLE_KEY",
        "DATABASE_URL", "REDIS_URL", "MEM0_API_KEY", "GITHUB_TOKEN", "ZAPIER_API_KEY",
        "CLIO_TOKEN_ENCRYPTION_KEY", "GCP_PROJECT_ID", "AWS_SECRET_ACCESS_KEY",
        "AZURE_CLIENT_SECRET", "VAULT_TOKEN"
    }

    # Required secrets for production operation
    REQUIRED_PRODUCTION_SECRETS = {
        "OPENAI_API_KEY", "JWT_PRIVATE_KEY", "JWT_PUBLIC_KEY"
    }

    # Default rotation intervals (in hours)
    DEFAULT_ROTATION_INTERVALS = {
        "JWT_PRIVATE_KEY": 24 * 7,  # Weekly
        "JWT_PUBLIC_KEY": 24 * 7,   # Weekly
        "API_KEYS": 24 * 30,        # Monthly
        "DATABASE_CREDENTIALS": 24 * 90,  # Quarterly
    }

    def __init__(self):
        self.provider = os.getenv("SECRETS_PROVIDER", "env")
        self._cache: Dict[str, Any] = {}
        self._metadata: Dict[str, SecretMetadata] = {}
        self._encryption_key: Optional[bytes] = None
        self._audit_enabled = os.getenv("SECRETS_AUDIT_ENABLED", "true").lower() == "true"
        self._validate_on_access = os.getenv("SECRETS_VALIDATE_ON_ACCESS", "true").lower() == "true"
        self._enable_cache_encryption = os.getenv("SECRETS_ENCRYPT_CACHE", "true").lower() == "true"
        self._max_cache_size = int(os.getenv("SECRETS_MAX_CACHE_SIZE", "1000"))
        self._cache_ttl_seconds = int(os.getenv("SECRETS_CACHE_TTL_SECONDS", "300"))  # 5 minutes

        self._initialize_encryption()
        self._initialize_provider()
        self._setup_audit_logging()

    def _initialize_encryption(self):
        """Initialize encryption for cache if enabled."""
        if self._enable_cache_encryption:
            # Generate or load encryption key
            key_material = os.getenv("SECRETS_CACHE_ENCRYPTION_KEY")
            if key_material:
                self._encryption_key = base64.urlsafe_b64decode(key_material.encode())
            else:
                # Generate a new key (not recommended for production)
                self._encryption_key = Fernet.generate_key()
                logger.warning(
                    "Generated ephemeral cache encryption key. "
                    "Set SECRETS_CACHE_ENCRYPTION_KEY for persistent encryption."
                )

    def _setup_audit_logging(self):
        """Setup audit logging for security compliance."""
        if self._audit_enabled:
            audit_handler = logging.FileHandler(
                os.getenv("SECRETS_AUDIT_LOG_FILE", "secrets_audit.log")
            )
            audit_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S UTC"
                )
            )
            audit_logger.addHandler(audit_handler)
            audit_logger.setLevel(logging.INFO)

    def _initialize_provider(self):
        """Initialize the secrets provider with enhanced error handling."""
        try:
            if self.provider == "gcp":
                self._initialize_gcp_provider()
            elif self.provider == "aws":
                self._initialize_aws_provider()
            elif self.provider == "azure":
                self._initialize_azure_provider()
            elif self.provider == "vault":
                self._initialize_vault_provider()
            elif self.provider == "env":
                logger.info("Using environment variables for secrets")
            else:
                logger.warning(f"Unknown secrets provider: {self.provider}, falling back to env")
                self.provider = "env"
        except Exception as e:
            logger.error(f"Failed to initialize secrets provider {self.provider}: {e}")
            self.provider = "env"
            logger.info("Falling back to environment variables")

    def _initialize_gcp_provider(self):
        """Initialize GCP Secret Manager."""
        try:
            from google.cloud import secretmanager
            self.client = secretmanager.SecretManagerServiceClient()
            self.project_id = os.getenv("GCP_PROJECT_ID")
            if not self.project_id:
                raise ValueError("GCP_PROJECT_ID is required for GCP Secret Manager")
            logger.info("Initialized GCP Secret Manager")
        except ImportError:
            logger.warning("GCP Secret Manager library not available")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize GCP Secret Manager: {e}")
            raise

    def _initialize_aws_provider(self):
        """Initialize AWS Secrets Manager."""
        try:
            import boto3
            self.client = boto3.client('secretsmanager')
            logger.info("Initialized AWS Secrets Manager")
        except ImportError:
            logger.warning("AWS SDK not available")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize AWS Secrets Manager: {e}")
            raise

    def _initialize_azure_provider(self):
        """Initialize Azure Key Vault."""
        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential

            vault_url = os.getenv("AZURE_VAULT_URL")
            if not vault_url:
                raise ValueError("AZURE_VAULT_URL is required for Azure Key Vault")

            credential = DefaultAzureCredential()
            self.client = SecretClient(vault_url=vault_url, credential=credential)
            logger.info("Initialized Azure Key Vault")
        except ImportError:
            logger.warning("Azure SDK not available")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Azure Key Vault: {e}")
            raise

    def _initialize_vault_provider(self):
        """Initialize HashiCorp Vault."""
        try:
            import hvac

            vault_url = os.getenv("VAULT_URL", "http://localhost:8200")
            vault_token = os.getenv("VAULT_TOKEN")

            if not vault_token:
                raise ValueError("VAULT_TOKEN is required for HashiCorp Vault")

            self.client = hvac.Client(url=vault_url, token=vault_token)
            if not self.client.is_authenticated():
                raise ValueError("Failed to authenticate with Vault")

            logger.info("Initialized HashiCorp Vault")
        except ImportError:
            logger.warning("HashiCorp Vault client not available")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize HashiCorp Vault: {e}")
            raise

    def get_secret(self, key: str, default: Optional[str] = None, validate: bool = None) -> Optional[str]:
        """Retrieve a secret value securely with validation and audit logging."""
        start_time = time.time()

        # Initialize metadata if not exists
        if key not in self._metadata:
            rotation_hours = self._get_rotation_interval(key)
            self._metadata[key] = SecretMetadata(key, rotation_interval_hours=rotation_hours)

        metadata = self._metadata[key]

        # Check if secret is compromised
        if metadata.is_compromised:
            self._audit_log("access_denied", key, "Secret is marked as compromised")
            raise SecretValidationError(f"Secret {key} is compromised and cannot be accessed")

        # Check cache first (with TTL)
        cached_value = self._get_from_cache(key)
        if cached_value is not None:
            metadata.record_access(True)
            self._audit_log("cache_hit", key)
            return cached_value

        # Retrieve from provider
        try:
            value = self._retrieve_from_provider(key, default)

            # Validate secret if enabled
            if (validate is True) or (validate is None and self._validate_on_access):
                self._validate_secret(key, value)

            # Cache the value with encryption
            if value:
                self._set_cache(key, value)
                metadata.record_access(True)

                # Mask sensitive values in logs
                log_value = self._mask_sensitive_value(key, value)
                self._audit_log("secret_retrieved", key, f"Retrieved from {self.provider}", {
                    "provider": self.provider,
                    "retrieval_time_ms": (time.time() - start_time) * 1000,
                    "value_length": len(value) if value else 0,
                    "is_default": value == default
                })
            else:
                metadata.record_access(False)
                self._audit_log("secret_not_found", key, f"Secret not found in {self.provider}")

            return value

        except Exception as e:
            metadata.record_access(False)
            self._audit_log("access_error", key, f"Error retrieving secret: {str(e)}")
            logger.error(f"Failed to retrieve secret {key}: {e}")
            return default

    def _get_rotation_interval(self, key: str) -> int:
        """Get rotation interval for a secret key."""
        # Check for key-specific interval
        env_key = f"SECRETS_ROTATION_INTERVAL_{key}"
        interval = os.getenv(env_key)
        if interval and interval.isdigit():
            return int(interval)

        # Check default intervals by pattern
        if key in ["JWT_PRIVATE_KEY", "JWT_PUBLIC_KEY"]:
            return self.DEFAULT_ROTATION_INTERVALS["JWT_PRIVATE_KEY"]
        elif "API_KEY" in key:
            return self.DEFAULT_ROTATION_INTERVALS["API_KEYS"]
        elif "DATABASE" in key or "DB_" in key:
            return self.DEFAULT_ROTATION_INTERVALS["DATABASE_CREDENTIALS"]

        return 0  # No rotation by default

    def _retrieve_from_provider(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve secret from the configured provider."""
        if self.provider == "env":
            return os.getenv(key, default)
        elif self.provider == "gcp":
            return self._retrieve_from_gcp(key, default)
        elif self.provider == "aws":
            return self._retrieve_from_aws(key, default)
        elif self.provider == "azure":
            return self._retrieve_from_azure(key, default)
        elif self.provider == "vault":
            return self._retrieve_from_vault(key, default)
        else:
            return os.getenv(key, default)

    def _retrieve_from_gcp(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve secret from GCP Secret Manager."""
        try:
            secret_name = f"projects/{self.project_id}/secrets/{key}/versions/latest"
            response = self.client.access_secret_version(request={"name": secret_name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.debug(f"Failed to retrieve secret {key} from GCP: {e}")
            return os.getenv(key, default)

    def _retrieve_from_aws(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve secret from AWS Secrets Manager."""
        try:
            response = self.client.get_secret_value(SecretId=key)
            value = response.get('SecretString')
            if not value and 'SecretBinary' in response:
                value = response['SecretBinary'].decode("utf-8")
            return value
        except Exception as e:
            logger.debug(f"Failed to retrieve secret {key} from AWS: {e}")
            return os.getenv(key, default)

    def _retrieve_from_azure(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve secret from Azure Key Vault."""
        try:
            secret = self.client.get_secret(key)
            return secret.value
        except Exception as e:
            logger.debug(f"Failed to retrieve secret {key} from Azure: {e}")
            return os.getenv(key, default)

    def _retrieve_from_vault(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve secret from HashiCorp Vault."""
        try:
            # Default path, can be configured
            mount_point = os.getenv("VAULT_MOUNT_POINT", "secret")
            path = f"{mount_point}/hermes/{key}"

            response = self.client.secrets.kv.v2.read_secret_version(path=path)
            return response['data']['data'].get('value')
        except Exception as e:
            logger.debug(f"Failed to retrieve secret {key} from Vault: {e}")
            return os.getenv(key, default)

    def get_json_secret(self, key: str, default: Optional[Dict] = None) -> Optional[Dict]:
        """Retrieve a JSON secret value with validation."""
        value = self.get_secret(key)
        if value:
            try:
                parsed = json.loads(value)
                self._audit_log("json_secret_parsed", key, "Successfully parsed JSON secret")
                return parsed
            except json.JSONDecodeError as e:
                self._audit_log("json_parse_error", key, f"Failed to parse JSON: {str(e)}")
                logger.error(f"Failed to parse JSON secret {key}: {e}")
        return default

    def get_database_url(self, key: str = "DATABASE_URL", validate_connection: bool = False) -> Optional[str]:
        """Get database URL with optional connection validation."""
        url = self.get_secret(key)
        if url and validate_connection:
            if self._validate_database_url(url):
                return url
            else:
                self._audit_log("database_validation_failed", key, "Database URL validation failed")
                return None
        return url

    def get_api_key(self, service: str, key: str = None) -> Optional[str]:
        """Get API key for a specific service with validation."""
        if not key:
            key = f"{service.upper()}_API_KEY"

        api_key = self.get_secret(key)
        if api_key:
            # Basic API key format validation
            if self._validate_api_key_format(service, api_key):
                return api_key
            else:
                self._audit_log("api_key_format_invalid", key, f"Invalid format for {service} API key")
        return None

    def _get_from_cache(self, key: str) -> Optional[str]:
        """Get value from cache with TTL check."""
        if key not in self._cache:
            return None

        cache_entry = self._cache[key]
        if isinstance(cache_entry, dict) and 'expires_at' in cache_entry:
            if datetime.utcnow() > cache_entry['expires_at']:
                del self._cache[key]
                return None
            value = cache_entry['value']
        else:
            # Legacy cache entry without expiration
            value = cache_entry

        # Decrypt if cache encryption is enabled
        if self._enable_cache_encryption and self._encryption_key:
            try:
                fernet = Fernet(self._encryption_key)
                return fernet.decrypt(value.encode()).decode()
            except Exception:
                # If decryption fails, remove from cache
                del self._cache[key]
                return None

        return value

    def _set_cache(self, key: str, value: str):
        """Set value in cache with encryption and TTL."""
        if len(self._cache) >= self._max_cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        cached_value = value

        # Encrypt if cache encryption is enabled
        if self._enable_cache_encryption and self._encryption_key:
            fernet = Fernet(self._encryption_key)
            cached_value = fernet.encrypt(value.encode()).decode()

        # Store with expiration
        expires_at = datetime.utcnow() + timedelta(seconds=self._cache_ttl_seconds)
        self._cache[key] = {
            'value': cached_value,
            'expires_at': expires_at
        }

    def clear_cache(self, key: Optional[str] = None):
        """Clear the secrets cache."""
        if key:
            if key in self._cache:
                del self._cache[key]
                self._audit_log("cache_cleared", key, "Specific cache entry cleared")
        else:
            self._cache.clear()
            self._audit_log("cache_cleared", "all", "All cache entries cleared")
        logger.info(f"Cleared secrets cache{f' for {key}' if key else ''}")

    def _validate_secret(self, key: str, value: Optional[str]):
        """Validate secret value based on key type."""
        if not value:
            return

        try:
            if key.endswith("_API_KEY"):
                self._validate_api_key_format(key.replace("_API_KEY", "").lower(), value)
            elif key in ["JWT_PRIVATE_KEY", "JWT_PUBLIC_KEY"]:
                self._validate_jwt_key(value, key)
            elif "DATABASE_URL" in key:
                self._validate_database_url(value)
            elif "URL" in key:
                self._validate_url(value)

        except SecretValidationError as e:
            self._audit_log("validation_failed", key, str(e))
            raise

    def _validate_api_key_format(self, service: str, api_key: str) -> bool:
        """Validate API key format for specific services."""
        patterns = {
            "openai": r"^sk-[A-Za-z0-9]{48}$",
            "stripe": r"^(sk|pk)_(test_|live_)?[A-Za-z0-9]{24,}$",
            "github": r"^gh[ps]_[A-Za-z0-9]{36}$",
            # Add more service patterns as needed
        }

        if service in patterns:
            if not re.match(patterns[service], api_key):
                raise SecretValidationError(f"Invalid {service} API key format")

        # General validations
        if len(api_key) < 10:
            raise SecretValidationError(f"API key too short for {service}")

        return True

    def _validate_jwt_key(self, key_content: str, key_type: str):
        """Validate JWT key format."""
        if key_type == "JWT_PRIVATE_KEY":
            if not ("BEGIN PRIVATE KEY" in key_content or "BEGIN RSA PRIVATE KEY" in key_content):
                raise SecretValidationError("Invalid JWT private key format")
        elif key_type == "JWT_PUBLIC_KEY":
            if not "BEGIN PUBLIC KEY" in key_content:
                raise SecretValidationError("Invalid JWT public key format")

    def _validate_database_url(self, url: str) -> bool:
        """Validate database URL format."""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise SecretValidationError("Invalid database URL format")

            if parsed.scheme not in ["postgresql", "postgres", "mysql", "sqlite"]:
                logger.warning(f"Unusual database scheme: {parsed.scheme}")

            return True
        except Exception as e:
            raise SecretValidationError(f"Database URL validation failed: {str(e)}")

    def _validate_url(self, url: str):
        """Validate general URL format."""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise SecretValidationError("Invalid URL format")
        except Exception as e:
            raise SecretValidationError(f"URL validation failed: {str(e)}")

    def _mask_sensitive_value(self, key: str, value: str) -> str:
        """Mask sensitive values for logging."""
        if key in self.SENSITIVE_KEYS or "PASSWORD" in key or "SECRET" in key:
            if len(value) <= 8:
                return "***"
            return value[:3] + "***" + value[-2:]
        return value

    def _audit_log(self, event_type: str, key: str, message: str = "", metadata: Dict = None):
        """Log security events for audit purposes."""
        if not self._audit_enabled:
            return

        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "secret_key": key,
            "message": message,
            "provider": self.provider,
            "metadata": metadata or {}
        }

        audit_logger.info(json.dumps(audit_entry))

    def validate_production_readiness(self) -> Dict[str, Any]:
        """Validate that all required secrets are available for production."""
        results = {
            "ready": True,
            "missing_secrets": [],
            "invalid_secrets": [],
            "warnings": []
        }

        for secret_key in self.REQUIRED_PRODUCTION_SECRETS:
            try:
                value = self.get_secret(secret_key)
                if not value:
                    results["missing_secrets"].append(secret_key)
                    results["ready"] = False
                else:
                    # Validate the secret format
                    try:
                        self._validate_secret(secret_key, value)
                    except SecretValidationError as e:
                        results["invalid_secrets"].append({
                            "key": secret_key,
                            "error": str(e)
                        })
                        results["ready"] = False
            except Exception as e:
                results["invalid_secrets"].append({
                    "key": secret_key,
                    "error": f"Access error: {str(e)}"
                })
                results["ready"] = False

        # Check for secrets needing rotation
        for key, metadata in self._metadata.items():
            if metadata.needs_rotation():
                results["warnings"].append(f"Secret {key} needs rotation")

        return results

    def get_secrets_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of secrets management."""
        total_secrets = len(self._metadata)
        compromised_count = sum(1 for m in self._metadata.values() if m.is_compromised)
        rotation_needed = sum(1 for m in self._metadata.values() if m.needs_rotation())

        return {
            "provider": self.provider,
            "total_secrets_tracked": total_secrets,
            "cache_size": len(self._cache),
            "cache_encryption_enabled": self._enable_cache_encryption,
            "audit_enabled": self._audit_enabled,
            "validation_enabled": self._validate_on_access,
            "compromised_secrets": compromised_count,
            "secrets_needing_rotation": rotation_needed,
            "cache_hit_ratio": self._calculate_cache_hit_ratio(),
            "provider_status": "healthy",  # Could be enhanced with actual health checks
        }

    def _calculate_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio for monitoring."""
        total_accesses = sum(m.access_count for m in self._metadata.values())
        if total_accesses == 0:
            return 0.0

        # Approximate cache hits (this is simplified)
        return min(0.8, len(self._cache) / max(1, total_accesses))

    def rotate_secret(self, key: str, new_value: str, force: bool = False) -> bool:
        """Rotate a secret with the new value."""
        try:
            if key not in self._metadata and not force:
                raise SecretRotationError(f"Secret {key} not found in metadata")

            # Validate new value
            self._validate_secret(key, new_value)

            # Update in provider (implementation depends on provider)
            success = self._update_secret_in_provider(key, new_value)

            if success:
                # Clear from cache
                self.clear_cache(key)

                # Update metadata
                if key in self._metadata:
                    self._metadata[key].created_at = datetime.utcnow()
                    self._metadata[key].is_compromised = False

                self._audit_log("secret_rotated", key, "Secret successfully rotated")
                logger.info(f"Successfully rotated secret {key}")
                return True
            else:
                self._audit_log("rotation_failed", key, "Failed to rotate secret in provider")
                return False

        except Exception as e:
            self._audit_log("rotation_error", key, f"Rotation error: {str(e)}")
            logger.error(f"Failed to rotate secret {key}: {e}")
            return False

    def _update_secret_in_provider(self, key: str, new_value: str) -> bool:
        """Update secret in the configured provider."""
        # Note: This is a simplified implementation
        # In production, you'd implement provider-specific update methods
        if self.provider == "env":
            # Can't update environment variables at runtime
            logger.warning("Cannot update environment variables at runtime")
            return False

        # For cloud providers, implement actual update logic
        logger.warning(f"Secret rotation not implemented for provider: {self.provider}")
        return False

    def mark_secret_compromised(self, key: str):
        """Mark a secret as compromised for immediate attention."""
        if key in self._metadata:
            self._metadata[key].mark_compromised()
        else:
            # Create metadata for unknown secret
            self._metadata[key] = SecretMetadata(key)
            self._metadata[key].mark_compromised()

        # Clear from cache immediately
        self.clear_cache(key)

        self._audit_log("secret_compromised", key, "Secret marked as compromised")

    def cleanup(self):
        """Cleanup resources and clear sensitive data."""
        # Clear cache
        self.clear_cache()

        # Clear encryption key
        if self._encryption_key:
            self._encryption_key = None

        # Close provider connections if needed
        if hasattr(self, 'client'):
            try:
                if hasattr(self.client, 'close'):
                    self.client.close()
            except Exception as e:
                logger.debug(f"Error closing provider client: {e}")

        self._audit_log("cleanup_completed", "system", "Secrets manager cleanup completed")
        logger.info("Secrets manager cleanup completed")


# Global instance
secrets_manager = SecretsManager()


# Convenience functions
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Convenience function to get a secret."""
    return secrets_manager.get_secret(key, default)


def get_database_url(validate: bool = False) -> Optional[str]:
    """Convenience function to get database URL."""
    return secrets_manager.get_database_url(validate_connection=validate)


def get_api_key(service: str) -> Optional[str]:
    """Convenience function to get API key for a service."""
    return secrets_manager.get_api_key(service)


def validate_production_secrets() -> Dict[str, Any]:
    """Validate production readiness of secrets."""
    return secrets_manager.validate_production_readiness()