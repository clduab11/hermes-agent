"""
TTS Interface and Base Classes

Defines the abstract interface that all TTS backends must implement.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TTSBackend(Enum):
    """Supported TTS backend engines."""
    KOKORO = "kokoro"
    OPENAI = "openai"
    EXISTING = "existing"  # Legacy/fallback backend


@dataclass
class SynthesisRequest:
    """Request for TTS synthesis."""
    text: str
    locale: str = "en-US"  # BCP 47 language tag (use hyphens, e.g., 'en-US', 'es-ES'; not underscores like 'en_US')
    voice_id: Optional[str] = None
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SynthesisResult:
    """Result from TTS synthesis."""
    audio_data: bytes
    format: str  # 'mp3', 'wav', 'pcm', etc.
    sample_rate: int
    duration_ms: int
    synthesis_time_ms: float
    locale: str
    voice_id: str
    backend: TTSBackend
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_low_latency(self) -> bool:
        """Check if synthesis met low-latency requirement (<500ms)."""
        return self.synthesis_time_ms < 500


class TTSInterface(ABC):
    """
    Abstract base class for TTS backends.
    
    All TTS implementations must inherit from this class and implement
    the required methods.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize TTS backend.
        
        Args:
            config: Backend-specific configuration
        """
        self.config = config
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the TTS backend.
        
        This method should load models, establish connections, etc.
        Must be called before synthesize().
        """
        pass

    @abstractmethod
    async def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        """
        Synthesize speech from text.
        
        Args:
            request: Synthesis request with text, locale, voice, etc.
            
        Returns:
            SynthesisResult with audio data and metadata
            
        Raises:
            TTSError: If synthesis fails
        """
        pass

    @abstractmethod
    async def get_available_voices(self, locale: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of available voices.
        
        Args:
            locale: Optional locale filter (e.g., 'en-US')
            
        Returns:
            List of voice metadata dictionaries
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if backend is healthy and ready.
        
        Returns:
            True if healthy, False otherwise
        """
        pass

    async def shutdown(self) -> None:
        """
        Shutdown the TTS backend and release resources.
        
        Default implementation does nothing. Override if cleanup is needed.
        """
        pass

    def get_backend_name(self) -> TTSBackend:
        """Get the backend type."""
        return self.config.get("backend", TTSBackend.EXISTING)


class TTSError(Exception):
    """Base exception for TTS errors."""
    pass


class TTSInitializationError(TTSError):
    """Raised when TTS backend initialization fails."""
    pass


class TTSSynthesisError(TTSError):
    """Raised when speech synthesis fails."""
    pass


class TTSUnsupportedLocaleError(TTSError):
    """Raised when requested locale is not supported."""
    pass


class TTSUnsupportedVoiceError(TTSError):
    """Raised when requested voice is not available."""
    pass
