"""Configuration management for HERMES voice agent system."""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host address")
    api_port: int = Field(default=8000, ge=1, le=65535, description="API port number")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # OpenAI Configuration
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4", description="OpenAI model to use")
    
    # Voice Configuration
    whisper_model: str = Field(default="base", description="Whisper model size")
    whisper_device: str = Field(default="cpu", description="Device for Whisper processing")
    kokoro_api_url: str = Field(default="http://localhost:8001", description="Kokoro TTS API URL")
    kokoro_voice: str = Field(default="af_sarah", description="Default voice for TTS")
    
    # Audio Configuration
    sample_rate: int = Field(default=16000, ge=8000, le=48000, description="Audio sample rate")
    chunk_size: int = Field(default=1024, ge=512, le=8192, description="Audio chunk size")
    max_audio_length_seconds: int = Field(default=30, ge=1, le=300, description="Max audio length")
    response_timeout: float = Field(default=0.1, ge=0.01, le=5.0, description="Response timeout")
    
    # Legal Compliance
    confidence_threshold: float = Field(default=0.85, ge=0.1, le=1.0, description="AI confidence threshold")
    enable_disclaimers: bool = Field(default=True, description="Enable legal disclaimers")
    audit_logging: bool = Field(default=True, description="Enable audit logging")
    
    # JWT Authentication
    jwt_private_key: str = Field(default="", description="JWT private key")
    jwt_public_key: str = Field(default="", description="JWT public key")
    jwt_algorithm: str = Field(default="RS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=15, ge=1, le=1440, description="Access token expiry")
    refresh_token_expire_days: int = Field(default=7, ge=1, le=30, description="Refresh token expiry")
    
    # Database Configuration
    database_url: Optional[str] = Field(default=None, description="Database connection URL")
    redis_url: Optional[str] = Field(default="redis://localhost:6379", description="Redis connection URL")
    
    # MCP Configuration
    clio_client_id: Optional[str] = Field(default=None, description="Clio OAuth client ID")
    clio_client_secret: Optional[str] = Field(default=None, description="Clio OAuth client secret") 
    clio_redirect_uri: Optional[str] = Field(default=None, description="Clio OAuth redirect URI")
    
    zapier_api_key: Optional[str] = Field(default=None, description="Zapier API key")
    github_token: Optional[str] = Field(default=None, description="GitHub access token")
    
    supabase_url: Optional[str] = Field(default=None, description="Supabase project URL")
    supabase_anon_key: Optional[str] = Field(default=None, description="Supabase anon key")
    supabase_service_role_key: Optional[str] = Field(default=None, description="Supabase service role key")
    
    mem0_api_key: Optional[str] = Field(default=None, description="Mem0 API key")


# Global settings instance
settings = Settings()
