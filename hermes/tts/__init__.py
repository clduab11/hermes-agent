"""
HERMES Text-to-Speech (TTS) Module

Provides a unified interface for multiple TTS backends including Kokoro and OpenAI.
Supports config-driven backend selection and multilingual voice synthesis.
"""

from .interface import (
    TTSInterface,
    TTSBackend,
    SynthesisRequest,
    SynthesisResult,
    TTSError,
    TTSInitializationError,
    TTSSynthesisError,
    TTSUnsupportedLocaleError,
    TTSUnsupportedVoiceError,
)
from .factory import get_tts_engine, TTSFactory, get_global_tts_engine, shutdown_global_tts_engine
from .kokoro import KokoroTTS
from .openai_tts import OpenAITTS
from .existing_adapter import ExistingTTSAdapter

__all__ = [
    # Interface and types
    "TTSInterface",
    "TTSBackend",
    "SynthesisRequest",
    "SynthesisResult",
    # Exceptions
    "TTSError",
    "TTSInitializationError",
    "TTSSynthesisError",
    "TTSUnsupportedLocaleError",
    "TTSUnsupportedVoiceError",
    # Factory
    "TTSFactory",
    "get_tts_engine",
    "get_global_tts_engine",
    "shutdown_global_tts_engine",
    # Backends
    "KokoroTTS",
    "OpenAITTS",
    "ExistingTTSAdapter",
]
