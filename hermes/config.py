"""Configuration management for HERMES voice agent system."""
from typing import Optional
import os

# Simple configuration class to avoid dependency issues
class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # API Configuration
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # OpenAI Configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
        
        # Voice Configuration
        self.whisper_model = os.getenv("WHISPER_MODEL", "base")
        self.whisper_device = os.getenv("WHISPER_DEVICE", "cpu")
        self.kokoro_api_url = os.getenv("KOKORO_API_URL", "http://localhost:8001")
        self.kokoro_voice = os.getenv("KOKORO_VOICE", "af_sarah")
        
        # Audio Configuration
        self.sample_rate = int(os.getenv("SAMPLE_RATE", "16000"))
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1024"))
        self.max_audio_length_seconds = int(os.getenv("MAX_AUDIO_LENGTH_SECONDS", "30"))
        self.response_timeout = float(os.getenv("RESPONSE_TIMEOUT_SECONDS", "0.1"))
        
        # Legal Compliance
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.85"))
        self.enable_disclaimers = os.getenv("ENABLE_DISCLAIMERS", "true").lower() == "true"
        self.audit_logging = os.getenv("AUDIT_LOGGING", "true").lower() == "true"
        
        # JWT Authentication
        self.jwt_private_key = os.getenv("JWT_PRIVATE_KEY", "")
        self.jwt_public_key = os.getenv("JWT_PUBLIC_KEY", "")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "RS256")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
        # MCP Configuration
        self.clio_client_id = os.getenv("CLIO_CLIENT_ID")
        self.clio_client_secret = os.getenv("CLIO_CLIENT_SECRET") 
        self.clio_redirect_uri = os.getenv("CLIO_REDIRECT_URI")
        
        self.zapier_api_key = os.getenv("ZAPIER_API_KEY")
        self.github_token = os.getenv("GITHUB_TOKEN")
        
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        self.mem0_api_key = os.getenv("MEM0_API_KEY")


# Global settings instance
settings = Settings()
