"""Configuration management for HERMES voice agent system."""

from typing import Any, Dict, List, Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .security.secrets_manager import secrets_manager
from .security.config_validator import config_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables with validation."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # API Configuration
    api_host: str = Field(default="127.0.0.1", description="API host address")
    api_port: int = Field(default=8000, ge=1, le=65535, description="API port number")
    debug: bool = Field(default=False, description="Enable debug mode")
    demo_mode: bool = Field(
        default=False, description="Enable demo features and mock data"
    )
    cors_allow_origins: Optional[str] = Field(
        default=None,
        description="Comma-separated list of allowed CORS origins (e.g. https://app.example.com,https://admin.example.com)",
    )

    # OpenAI Configuration
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4", description="OpenAI model to use")

    @property
    def secure_openai_api_key(self) -> str:
        """Get OpenAI API key from secure secrets manager."""
        return secrets_manager.get_api_key("openai") or self.openai_api_key

    # Voice Configuration
    whisper_model: str = Field(default="base", description="Whisper model size")
    whisper_device: str = Field(
        default="cpu", description="Device for Whisper processing"
    )
    kokoro_api_url: str = Field(
        default="http://localhost:8001", description="Kokoro TTS API URL"
    )
    kokoro_voice: str = Field(default="af_sarah", description="Default voice for TTS")

    # Audio Configuration
    sample_rate: int = Field(
        default=16000, ge=8000, le=48000, description="Audio sample rate"
    )
    chunk_size: int = Field(
        default=1024, ge=512, le=8192, description="Audio chunk size"
    )
    max_audio_length_seconds: int = Field(
        default=30, ge=1, le=300, description="Max audio length"
    )
    response_timeout: float = Field(
        default=0.1,
        ge=0.01,
        le=5.0,
        description="Response timeout (seconds)",
        validation_alias=AliasChoices("RESPONSE_TIMEOUT", "RESPONSE_TIMEOUT_SECONDS"),
    )

    # Legal Compliance
    confidence_threshold: float = Field(
        default=0.85, ge=0.1, le=1.0, description="AI confidence threshold"
    )
    enable_disclaimers: bool = Field(
        default=True, description="Enable legal disclaimers"
    )
    audit_logging: bool = Field(default=True, description="Enable audit logging")

    # JWT Authentication
    jwt_private_key: str = Field(default="", description="JWT private key")
    jwt_public_key: str = Field(default="", description="JWT public key")

    @property
    def secure_jwt_private_key(self) -> str:
        """Get JWT private key from secure secrets manager."""
        return secrets_manager.get_secret("JWT_PRIVATE_KEY") or self.jwt_private_key

    @property
    def secure_jwt_public_key(self) -> str:
        """Get JWT public key from secure secrets manager."""
        return secrets_manager.get_secret("JWT_PUBLIC_KEY") or self.jwt_public_key
    jwt_algorithm: str = Field(default="RS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=15, ge=1, le=1440, description="Access token expiry"
    )
    refresh_token_expire_days: int = Field(
        default=7, ge=1, le=30, description="Refresh token expiry"
    )

    # Database Configuration
    database_url: Optional[str] = Field(
        default=None, description="Database connection URL"
    )
    redis_url: Optional[str] = Field(
        default="redis://localhost:6379", description="Redis connection URL"
    )

    @property
    def secure_database_url(self) -> Optional[str]:
        """Get database URL from secure secrets manager."""
        return secrets_manager.get_database_url() or self.database_url

    @property
    def secure_redis_url(self) -> Optional[str]:
        """Get Redis URL from secure secrets manager."""
        return secrets_manager.get_secret("REDIS_URL") or self.redis_url

    # MCP Configuration
    clio_client_id: Optional[str] = Field(
        default=None, description="Clio OAuth client ID"
    )
    clio_client_secret: Optional[str] = Field(
        default=None, description="Clio OAuth client secret"
    )
    clio_redirect_uri: Optional[str] = Field(
        default=None, description="Clio OAuth redirect URI"
    )
    clio_token_encryption_key: Optional[str] = Field(
        default=None, description="Base64-encoded Fernet key for encrypting Clio tokens"
    )

    zapier_api_key: Optional[str] = Field(default=None, description="Zapier API key")
    github_token: Optional[str] = Field(default=None, description="GitHub access token")

    supabase_url: Optional[str] = Field(
        default=None, description="Supabase project URL"
    )
    supabase_anon_key: Optional[str] = Field(
        default=None, description="Supabase anon key"
    )
    supabase_service_role_key: Optional[str] = Field(
        default=None, description="Supabase service role key"
    )

    mem0_api_key: Optional[str] = Field(default=None, description="Mem0 API key")

    # Billing Configuration
    stripe_api_key: Optional[str] = Field(default=None, description="Stripe API key")
    stripe_webhook_secret: Optional[str] = Field(
        default=None, description="Stripe webhook signing secret"
    )
    stripe_price_pro: Optional[str] = Field(
        default=None, description="Stripe price ID for Professional plan"
    )
    stripe_price_enterprise: Optional[str] = Field(
        default=None, description="Stripe price ID for Enterprise plan"
    )
    stripe_overage_price: Optional[str] = Field(
        default=None, description="Stripe price ID for interaction overage"
    )
    stripe_trial_days: int = Field(
        default=14, ge=0, description="Trial period length in days"
    )

    # Secure property accessors for sensitive configuration
    @property
    def secure_clio_client_secret(self) -> Optional[str]:
        """Get Clio client secret from secure secrets manager."""
        return secrets_manager.get_secret("CLIO_CLIENT_SECRET") or self.clio_client_secret

    @property
    def secure_clio_token_encryption_key(self) -> Optional[str]:
        """Get Clio token encryption key from secure secrets manager."""
        return secrets_manager.get_secret("CLIO_TOKEN_ENCRYPTION_KEY") or self.clio_token_encryption_key

    @property
    def secure_zapier_api_key(self) -> Optional[str]:
        """Get Zapier API key from secure secrets manager."""
        return secrets_manager.get_api_key("zapier") or self.zapier_api_key

    @property
    def secure_github_token(self) -> Optional[str]:
        """Get GitHub token from secure secrets manager."""
        return secrets_manager.get_secret("GITHUB_TOKEN") or self.github_token

    @property
    def secure_supabase_service_role_key(self) -> Optional[str]:
        """Get Supabase service role key from secure secrets manager."""
        return secrets_manager.get_secret("SUPABASE_SERVICE_ROLE_KEY") or self.supabase_service_role_key

    @property
    def secure_mem0_api_key(self) -> Optional[str]:
        """Get Mem0 API key from secure secrets manager."""
        return secrets_manager.get_api_key("mem0") or self.mem0_api_key

    @property
    def secure_stripe_api_key(self) -> Optional[str]:
        """Get Stripe API key from secure secrets manager."""
        return secrets_manager.get_api_key("stripe") or self.stripe_api_key

    @property
    def secure_stripe_webhook_secret(self) -> Optional[str]:
        """Get Stripe webhook secret from secure secrets manager."""
        return secrets_manager.get_secret("STRIPE_WEBHOOK_SECRET") or self.stripe_webhook_secret

    def validate_production_config(self) -> Dict[str, Any]:
        """Validate configuration for production deployment."""
        return config_validator.validate_production_deployment()

    def get_security_report(self) -> str:
        """Generate comprehensive security report."""
        return config_validator.generate_security_report()


# Backward compatibility alias for legacy attribute name
def _get_max_audio_length(self) -> int:
    return self.max_audio_length_seconds


Settings.max_audio_length = property(_get_max_audio_length)  # type: ignore[attr-defined]

# Global settings instance
settings = Settings()


def get_cors_origins_list() -> List[str]:
    """Parse and return allowed CORS origins as a list.

    Always includes GitHub Pages for demo, plus configured origins.
    Returns ["*"] only in debug mode with no specific configuration.
    """
    # Always include GitHub Pages URL for the demo
    github_pages_origin = "https://clduab11.github.io"
    origins = [github_pages_origin]
    
    if settings.cors_allow_origins:
        configured_origins = [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
        origins.extend(configured_origins)
    elif settings.debug:
        # In debug mode without specific config, allow localhost only for security
        return ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"]
    
    # Add development origins if in debug or demo mode
    if settings.debug or settings.demo_mode:
        dev_origins = [
            "http://localhost:3000",
            "http://localhost:5173",  # Vite default
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8000",
        ]
        origins.extend(dev_origins)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_origins = []
    for origin in origins:
        if origin not in seen:
            seen.add(origin)
            unique_origins.append(origin)
    
    return unique_origins
