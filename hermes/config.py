"""Configuration management for HERMES voice agent system."""
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # OpenAI Configuration
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", alias="OPENAI_MODEL")
    
    # Whisper Configuration
    whisper_model: str = Field(default="base", alias="WHISPER_MODEL")
    whisper_device: str = Field(default="cpu", alias="WHISPER_DEVICE")
    
    # Kokoro TTS Configuration
    kokoro_api_url: str = Field(default="http://localhost:8001", alias="KOKORO_API_URL")
    kokoro_voice: str = Field(default="af_sarah", alias="KOKORO_VOICE")
    
    # Audio Configuration
    sample_rate: int = Field(default=16000, alias="SAMPLE_RATE")
    chunk_size: int = Field(default=1024, alias="CHUNK_SIZE")
    
    # Performance Configuration
    max_audio_length: int = Field(default=30, alias="MAX_AUDIO_LENGTH_SECONDS")
    response_timeout: float = Field(default=0.1, alias="RESPONSE_TIMEOUT_SECONDS")
    
    # Legal Compliance
    confidence_threshold: float = Field(default=0.85, alias="CONFIDENCE_THRESHOLD")
    enable_disclaimers: bool = Field(default=True, alias="ENABLE_DISCLAIMERS")
    audit_logging: bool = Field(default=True, alias="AUDIT_LOGGING")

    # JWT Authentication
    jwt_private_key: str = Field(default="", alias="JWT_PRIVATE_KEY")
    jwt_public_key: str = Field(default="", alias="JWT_PUBLIC_KEY")
    jwt_algorithm: str = Field(default="RS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # MCP Configuration
    clio_client_id: Optional[str] = Field(default=None, alias="CLIO_CLIENT_ID")
    clio_client_secret: Optional[str] = Field(default=None, alias="CLIO_CLIENT_SECRET")
    clio_redirect_uri: Optional[str] = Field(default=None, alias="CLIO_REDIRECT_URI")
    
    zapier_api_key: Optional[str] = Field(default=None, alias="ZAPIER_API_KEY")
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")
    
    supabase_url: Optional[str] = Field(default=None, alias="SUPABASE_URL")
    supabase_anon_key: Optional[str] = Field(default=None, alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: Optional[str] = Field(default=None, alias="SUPABASE_SERVICE_ROLE_KEY")
    
    mem0_api_key: Optional[str] = Field(default=None, alias="MEM0_API_KEY")


# Global settings instance
settings = Settings()
