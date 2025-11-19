"""
OpenAI TTS Backend Implementation

Provides high-quality voice synthesis using OpenAI's TTS API.
"""

import logging
import time
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:
    httpx = None

from .interface import (
    TTSBackend,
    TTSInitializationError,
    TTSInterface,
    TTSSynthesisError,
    TTSUnsupportedLocaleError,
    SynthesisRequest,
    SynthesisResult,
)

logger = logging.getLogger(__name__)


class OpenAITTS(TTSInterface):
    """
    OpenAI TTS backend implementation.

    Uses OpenAI's text-to-speech API for high-quality voice synthesis.
    Supports multiple voices and languages.
    """

    # OpenAI TTS voices
    VOICES = {
        "alloy": {"gender": "neutral", "style": "balanced"},
        "echo": {"gender": "male", "style": "warm"},
        "fable": {"gender": "neutral", "style": "expressive"},
        "onyx": {"gender": "male", "style": "deep"},
        "nova": {"gender": "female", "style": "friendly"},
        "shimmer": {"gender": "female", "style": "clear"},
    }

    # Supported locales (OpenAI supports many languages automatically)
    SUPPORTED_LOCALES = [
        "en-US", "en-GB", "en-AU",
        "es-ES", "es-MX",
        "fr-FR", "fr-CA",
        "de-DE",
        "it-IT",
        "pt-PT", "pt-BR",
        "ja-JP",
        "ko-KR",
        "zh-CN", "zh-TW",
        "ar-SA",
        "hi-IN",
        "ru-RU",
        "pl-PL",
        "nl-NL",
        "tr-TR",
    ]

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenAI TTS backend.

        Args:
            config: Configuration dictionary with:
                - api_key: OpenAI API key (required)
                - model: TTS model ('tts-1' or 'tts-1-hd', default 'tts-1')
                - default_voice: Default voice to use (default 'nova')
                - response_format: Audio format ('mp3', 'opus', 'aac', 'flac')
        """
        super().__init__(config)
        self.api_key = config.get("api_key") or config.get("openai_api_key")
        self.model = config.get("model", "tts-1")
        self.default_voice = config.get("default_voice", "nova")
        self.response_format = config.get("response_format", "mp3")
        self._client = None

    async def initialize(self) -> None:
        """
        Initialize OpenAI TTS client.

        Raises:
            TTSInitializationError: If initialization fails
        """
        try:
            if httpx is None:
                raise TTSInitializationError(
                    "httpx library is required for OpenAI TTS. "
                    "Install it with: pip install httpx"
                )

            if not self.api_key:
                raise TTSInitializationError(
                    "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
                    "or pass 'api_key' in config."
                )

            logger.info(f"Initializing OpenAI TTS (model: {self.model})")

            self._client = httpx.AsyncClient(
                base_url="https://api.openai.com/v1",
                timeout=60.0,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )

            # Verify API key works by checking models endpoint
            response = await self._client.get("/models")
            if response.status_code == 401:
                raise TTSInitializationError("Invalid OpenAI API key")

            self._initialized = True
            logger.info("OpenAI TTS initialized successfully")

        except TTSInitializationError:
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI TTS: {e}")
            raise TTSInitializationError(f"OpenAI TTS initialization failed: {e}")

    async def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        """
        Synthesize speech using OpenAI TTS API.

        Args:
            request: Synthesis request

        Returns:
            SynthesisResult with audio data

        Raises:
            TTSSynthesisError: If synthesis fails
        """
        if not self._initialized:
            raise TTSSynthesisError("OpenAI TTS not initialized. Call initialize() first.")

        start_time = time.perf_counter()

        try:
            # Select voice (map voice_id to OpenAI voice or use default)
            voice = self._map_voice(request.voice_id) if request.voice_id else self.default_voice

            # Prepare request payload
            payload = {
                "model": self.model,
                "input": request.text,
                "voice": voice,
                "response_format": self.response_format,
                "speed": request.speed
            }

            # Make API request
            response = await self._client.post("/audio/speech", json=payload)

            if response.status_code != 200:
                error_detail = response.text
                raise TTSSynthesisError(
                    f"OpenAI TTS API error ({response.status_code}): {error_detail}"
                )

            audio_data = response.content
            synthesis_time_ms = (time.perf_counter() - start_time) * 1000

            # Estimate audio duration (rough calculation: ~150 words/minute)
            word_count = len(request.text.split())
            estimated_duration_ms = int((word_count / 150) * 60 * 1000 / request.speed)

            # Determine sample rate based on format
            sample_rate = 24000  # OpenAI TTS default

            result = SynthesisResult(
                audio_data=audio_data,
                format=self.response_format,
                sample_rate=sample_rate,
                duration_ms=estimated_duration_ms,
                synthesis_time_ms=synthesis_time_ms,
                locale=request.locale,
                voice_id=voice,
                backend=TTSBackend.OPENAI,
                metadata={
                    "text_length": len(request.text),
                    "word_count": word_count,
                    "speed": request.speed,
                    "model": self.model
                }
            )

            if not result.is_low_latency:
                logger.warning(
                    f"OpenAI TTS synthesis exceeded latency target: {synthesis_time_ms:.1f}ms > 500ms"
                )

            logger.info(
                f"OpenAI TTS synthesis completed: {synthesis_time_ms:.1f}ms, "
                f"{estimated_duration_ms}ms audio, voice={voice}"
            )

            return result

        except TTSSynthesisError:
            raise
        except Exception as e:
            logger.error(f"OpenAI TTS synthesis failed: {e}")
            raise TTSSynthesisError(f"Synthesis failed: {e}")

    async def get_available_voices(self, locale: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get available OpenAI TTS voices.

        Args:
            locale: Optional locale filter (not used for OpenAI as voices are multilingual)

        Returns:
            List of voice metadata
        """
        voices = []

        for voice_id, props in self.VOICES.items():
            voices.append({
                "id": voice_id,
                "locale": "multilingual",
                "gender": props["gender"],
                "style": props["style"],
                "is_default": voice_id == self.default_voice
            })

        return voices

    async def health_check(self) -> bool:
        """
        Check OpenAI TTS backend health.

        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self._initialized or not self._client:
                return False

            # Simple API check
            response = await self._client.get("/models")
            return response.status_code == 200

        except Exception as e:
            logger.error(f"OpenAI TTS health check failed: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown OpenAI TTS backend and release resources."""
        if self._client:
            await self._client.aclose()
            self._client = None

        self._initialized = False
        logger.info("OpenAI TTS shutdown complete")

    def _map_voice(self, voice_id: str) -> str:
        """
        Map voice_id to OpenAI voice name.

        Args:
            voice_id: Voice identifier

        Returns:
            OpenAI voice name
        """
        # If it's already an OpenAI voice, use it directly
        if voice_id.lower() in self.VOICES:
            return voice_id.lower()

        # Map common voice types to OpenAI voices
        voice_lower = voice_id.lower()

        if "female" in voice_lower and "friendly" in voice_lower:
            return "nova"
        elif "female" in voice_lower:
            return "shimmer"
        elif "male" in voice_lower and "deep" in voice_lower:
            return "onyx"
        elif "male" in voice_lower:
            return "echo"
        elif "expressive" in voice_lower:
            return "fable"
        else:
            return self.default_voice
