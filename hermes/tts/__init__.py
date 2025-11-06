"""
HERMES Text-to-Speech (TTS) Module

Provides a unified interface for multiple TTS backends including Kokoro and OpenAI.
Supports config-driven backend selection and multilingual voice synthesis.
"""

from .interface import TTSInterface, TTSBackend, SynthesisRequest, SynthesisResult
from .factory import get_tts_engine

__all__ = [
    "TTSInterface",
    "TTSBackend",
    "SynthesisRequest",
    "SynthesisResult",
    "get_tts_engine",
]
