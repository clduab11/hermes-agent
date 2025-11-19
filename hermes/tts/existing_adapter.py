"""
Existing TTS Adapter

Wraps the legacy text_to_speech.KokoroTTS implementation to conform
to the new TTSInterface. Provides backward compatibility.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from .interface import (
    TTSBackend,
    TTSInitializationError,
    TTSInterface,
    TTSSynthesisError,
    SynthesisRequest,
    SynthesisResult,
)

logger = logging.getLogger(__name__)


class ExistingTTSAdapter(TTSInterface):
    """
    Adapter for the legacy KokoroTTS implementation.

    This adapter wraps the existing text_to_speech.KokoroTTS class
    to provide compatibility with the new TTS interface.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the existing TTS adapter.

        Args:
            config: Configuration dictionary (passed to underlying implementation)
        """
        super().__init__(config)
        self._tts = None

    async def initialize(self) -> None:
        """
        Initialize the underlying KokoroTTS client.

        Raises:
            TTSInitializationError: If initialization fails
        """
        try:
            # Import here to avoid circular imports
            from hermes.text_to_speech import KokoroTTS

            logger.info("Initializing existing TTS adapter (legacy KokoroTTS)")

            self._tts = KokoroTTS()
            await self._tts.initialize()

            self._initialized = True
            logger.info("Existing TTS adapter initialized successfully")

        except ImportError as e:
            logger.error(f"Failed to import legacy KokoroTTS: {e}")
            raise TTSInitializationError(
                f"Could not import legacy TTS implementation: {e}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize existing TTS adapter: {e}")
            raise TTSInitializationError(f"Existing TTS initialization failed: {e}")

    async def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        """
        Synthesize speech using the legacy KokoroTTS.

        Args:
            request: Synthesis request

        Returns:
            SynthesisResult with audio data

        Raises:
            TTSSynthesisError: If synthesis fails
        """
        if not self._initialized or not self._tts:
            raise TTSSynthesisError(
                "Existing TTS not initialized. Call initialize() first."
            )

        start_time = time.perf_counter()

        try:
            # Preprocess text
            processed_text = await self._tts.preprocess_text(request.text)

            # Synthesize using legacy implementation
            result = await self._tts.synthesize_text(
                text=processed_text,
                voice=request.voice_id
            )

            synthesis_time_ms = (time.perf_counter() - start_time) * 1000

            # Convert legacy result to new format
            return SynthesisResult(
                audio_data=result.audio_data,
                format="wav",  # Legacy implementation uses WAV
                sample_rate=result.sample_rate,
                duration_ms=int(result.duration * 1000),
                synthesis_time_ms=synthesis_time_ms,
                locale=request.locale,
                voice_id=request.voice_id or "default",
                backend=TTSBackend.EXISTING,
                metadata={
                    "text_length": len(request.text),
                    "processing_time": result.processing_time,
                    "adapter": "legacy_kokoro"
                }
            )

        except Exception as e:
            logger.error(f"Existing TTS synthesis failed: {e}")
            raise TTSSynthesisError(f"Synthesis failed: {e}")

    async def get_available_voices(self, locale: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get available voices from the legacy implementation.

        Args:
            locale: Optional locale filter

        Returns:
            List of voice metadata
        """
        if not self._initialized or not self._tts:
            return []

        try:
            voices_data = await self._tts.get_available_voices()

            # Convert to standard format
            voices = []
            if isinstance(voices_data, dict):
                for voice_id, props in voices_data.items():
                    voice_info = {
                        "id": voice_id,
                        "locale": "en-US",  # Default locale
                        "is_default": False
                    }
                    if isinstance(props, dict):
                        voice_info.update(props)
                    voices.append(voice_info)

            return voices

        except Exception as e:
            logger.error(f"Failed to get voices from existing TTS: {e}")
            return []

    async def health_check(self) -> bool:
        """
        Check if the legacy TTS backend is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self._initialized or not self._tts:
                return False

            # Try to get voices as a health check
            await self._tts.get_available_voices()
            return True

        except Exception as e:
            logger.error(f"Existing TTS health check failed: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown the legacy TTS backend and release resources."""
        if self._tts:
            await self._tts.cleanup()
            self._tts = None

        self._initialized = False
        logger.info("Existing TTS adapter shutdown complete")
