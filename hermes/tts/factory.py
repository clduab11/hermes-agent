"""
TTS Factory for Backend Selection

Provides config-driven selection and instantiation of TTS backends.
"""

import logging
import os
from typing import Any, Dict, Optional

from .interface import TTSBackend, TTSInterface
from .kokoro import KokoroTTS
from .openai_tts import OpenAITTS
from .existing_adapter import ExistingTTSAdapter

logger = logging.getLogger(__name__)


class TTSFactory:
    """Factory for creating TTS backend instances."""

    @staticmethod
    def create(
        backend: Optional[TTSBackend] = None,
        config: Optional[Dict[str, Any]] = None,
        fallback_backend: Optional[TTSBackend] = None
    ) -> TTSInterface:
        """
        Create a TTS backend instance based on configuration.
        
        Args:
            backend: TTS backend to use (overrides config)
            config: Backend configuration dict
            fallback_backend: Fallback backend if primary fails
            
        Returns:
            Initialized TTS backend instance
            
        Raises:
            ValueError: If backend is not supported or configuration is invalid
        """
        config = config or {}
        
        # Determine backend from parameter, config, or environment
        if backend is None:
            backend_str = config.get("backend") or os.getenv("TTS_BACKEND", "kokoro")
            try:
                backend = TTSBackend(backend_str.lower())
            except ValueError:
                logger.warning(f"Unknown TTS backend '{backend_str}', defaulting to Kokoro")
                backend = TTSBackend.KOKORO
        
        # Set fallback if specified
        if fallback_backend is None:
            fallback_str = config.get("fallback_backend") or os.getenv("TTS_FALLBACK_BACKEND")
            if fallback_str:
                try:
                    fallback_backend = TTSBackend(fallback_str.lower())
                except ValueError:
                    logger.warning(f"Unknown fallback backend '{fallback_str}'")
                    fallback_backend = None
        
        logger.info(f"Creating TTS backend: {backend.value}" + 
                   (f" (fallback: {fallback_backend.value})" if fallback_backend else ""))
        
        try:
            # Create primary backend
            if backend == TTSBackend.KOKORO:
                return KokoroTTS(config)
            elif backend == TTSBackend.OPENAI:
                # Ensure OpenAI API key is available
                if "api_key" not in config and "openai_api_key" not in config:
                    openai_key = os.getenv("OPENAI_API_KEY")
                    if openai_key:
                        config["api_key"] = openai_key
                return OpenAITTS(config)
            elif backend == TTSBackend.EXISTING:
                # Legacy TTS backend integration
                return ExistingTTSAdapter(config)
            else:
                raise ValueError(f"Unsupported TTS backend: {backend}")
                
        except NotImplementedError as e:
            logger.warning(f"Backend not implemented: {e}")
            
            # Try fallback if available
            if fallback_backend and fallback_backend != backend:
                logger.info(f"Attempting fallback to {fallback_backend.value}")
                return TTSFactory.create(backend=fallback_backend, config=config, fallback_backend=None)
            
            # No fallback available
            raise ValueError(
                f"TTS backend '{backend.value}' failed to initialize and no fallback is configured. "
                f"Available backends: kokoro, openai, existing"
            ) from e
                
        except Exception as e:
            logger.error(f"Failed to create TTS backend '{backend.value}': {e}")
            
            # Try fallback if available
            if fallback_backend and fallback_backend != backend:
                logger.info(f"Attempting fallback to {fallback_backend.value}")
                return TTSFactory.create(backend=fallback_backend, config=config, fallback_backend=None)
            
            raise


def get_tts_engine(config: Optional[Dict[str, Any]] = None) -> TTSInterface:
    """
    Get a TTS engine instance with automatic configuration.
    
    Configuration priority:
    1. Passed config dict
    2. Environment variables
    3. Default values
    
    Environment variables:
    - TTS_BACKEND: Backend to use ('kokoro', 'openai', 'existing')
    - TTS_FALLBACK_BACKEND: Fallback if primary fails
    - KOKORO_API_URL: Kokoro API endpoint (if using API mode)
    - KOKORO_API_KEY: Kokoro API key
    - KOKORO_MODEL_PATH: Local model path (if using local mode)
    - OPENAI_API_KEY: OpenAI API key (for OpenAI backend)
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        TTS backend instance
        
    Example:
        >>> # Use default (Kokoro) backend
        >>> tts = get_tts_engine()
        >>> await tts.initialize()
        >>> result = await tts.synthesize(SynthesisRequest(
        ...     text="Hello, world!",
        ...     locale="en-US"
        ... ))
        
        >>> # Use specific backend with config
        >>> config = {
        ...     "backend": "kokoro",
        ...     "api_url": "https://kokoro-api.example.com",
        ...     "api_key": "your-api-key"
        ... }
        >>> tts = get_tts_engine(config)
    """
    if config is None:
        config = {}
    
    # Load configuration from environment if not in config dict
    if "backend" not in config:
        config["backend"] = os.getenv("TTS_BACKEND", "kokoro")
    
    if "fallback_backend" not in config:
        fallback = os.getenv("TTS_FALLBACK_BACKEND")
        if fallback:
            config["fallback_backend"] = fallback
    
    # Kokoro-specific environment variables
    if "api_url" not in config:
        kokoro_api_url = os.getenv("KOKORO_API_URL")
        if kokoro_api_url:
            config["api_url"] = kokoro_api_url
    
    if "api_key" not in config:
        kokoro_api_key = os.getenv("KOKORO_API_KEY")
        if kokoro_api_key:
            config["api_key"] = kokoro_api_key
    
    if "model_path" not in config:
        model_path = os.getenv("KOKORO_MODEL_PATH")
        if model_path:
            config["model_path"] = model_path
    
    return TTSFactory.create(config=config)


# Global TTS engine instance (lazy-loaded)
_tts_engine: Optional[TTSInterface] = None


async def get_global_tts_engine() -> TTSInterface:
    """
    Get or create the global TTS engine instance.
    
    Returns:
        Global TTS engine instance (initialized)
    """
    global _tts_engine
    
    if _tts_engine is None:
        _tts_engine = get_tts_engine()
        await _tts_engine.initialize()
    
    return _tts_engine


async def shutdown_global_tts_engine() -> None:
    """Shutdown the global TTS engine if it exists."""
    global _tts_engine
    
    if _tts_engine is not None:
        await _tts_engine.shutdown()
        _tts_engine = None
