"""
Configuration management for HERMES voice agent system.
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    
    # Whisper Configuration
    whisper_model: str = Field(default="base", env="WHISPER_MODEL")
    whisper_device: str = Field(default="cpu", env="WHISPER_DEVICE")
    
    # Kokoro TTS Configuration
    kokoro_api_url: str = Field(default="http://localhost:8001", env="KOKORO_API_URL")
    kokoro_voice: str = Field(default="af_sarah", env="KOKORO_VOICE")
    
    # Audio Configuration
    sample_rate: int = Field(default=16000, env="SAMPLE_RATE")
    chunk_size: int = Field(default=1024, env="CHUNK_SIZE")
    
    # Performance Configuration
    max_audio_length: int = Field(default=30, env="MAX_AUDIO_LENGTH_SECONDS")
    response_timeout: float = Field(default=0.1, env="RESPONSE_TIMEOUT_SECONDS")
    
    # Legal Compliance
    confidence_threshold: float = Field(default=0.85, env="CONFIDENCE_THRESHOLD")
    enable_disclaimers: bool = Field(default=True, env="ENABLE_DISCLAIMERS")
    audit_logging: bool = Field(default=True, env="AUDIT_LOGGING")
    
    # MCP Configuration
    clio_client_id: Optional[str] = Field(default=None, env="CLIO_CLIENT_ID")
    clio_client_secret: Optional[str] = Field(default=None, env="CLIO_CLIENT_SECRET")
    clio_redirect_uri: Optional[str] = Field(default=None, env="CLIO_REDIRECT_URI")
    
    zapier_api_key: Optional[str] = Field(default=None, env="ZAPIER_API_KEY")
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    
    supabase_url: Optional[str] = Field(default=None, env="SUPABASE_URL")
    supabase_anon_key: Optional[str] = Field(default=None, env="SUPABASE_ANON_KEY")
    supabase_service_role_key: Optional[str] = Field(default=None, env="SUPABASE_SERVICE_ROLE_KEY")
    
    mem0_api_key: Optional[str] = Field(default=None, env="MEM0_API_KEY")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }


# Global settings instance
settings = Settings()