"""
Speech-to-Text implementation using OpenAI Whisper.
"""
import asyncio
import io
import logging
import time
from typing import Optional, Dict, Any

import numpy as np

try:  # Optional heavy dependencies
    import whisper  # type: ignore
except Exception:  # pragma: no cover - handled gracefully
    whisper = None  # type: ignore

try:
    import torch  # type: ignore
except Exception:  # pragma: no cover - handled gracefully
    torch = None  # type: ignore
from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)


class TranscriptionResult(BaseModel):
    """Result of speech-to-text transcription."""
    text: str
    confidence: float
    language: str
    processing_time: float


class WhisperSTT:
    """Speech-to-text processor using OpenAI Whisper."""
    
    def __init__(self) -> None:
        self._model: Optional[Any] = None
        self._device = settings.whisper_device
        self._model_name = settings.whisper_model
        
    async def initialize(self) -> None:
        """Initialize the Whisper model."""
        logger.info(f"Loading Whisper model: {self._model_name} on {self._device}")
        
        # Run model loading in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        self._model = await loop.run_in_executor(
            None, 
            self._load_model
        )
        
        logger.info("Whisper model loaded successfully")
    
    def _load_model(self) -> Any:
        """Load the Whisper model synchronously."""
        if whisper is None:
            raise ImportError("whisper library is required for speech-to-text")
        return whisper.load_model(self._model_name, device=self._device)
    
    async def transcribe_audio(self, audio_data: bytes) -> TranscriptionResult:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio bytes (WAV format expected)
            
        Returns:
            TranscriptionResult with transcribed text and metadata
        """
        if not self._model:
            raise RuntimeError("Whisper model not initialized. Call initialize() first.")
        
        start_time = time.time()
        
        try:
            # Convert bytes to numpy array for Whisper
            audio_array = self._prepare_audio(audio_data)
            
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._transcribe_sync,
                audio_array
            )
            
            processing_time = time.time() - start_time
            
            # Extract confidence score (if available)
            confidence = self._calculate_confidence(result)
            
            transcription_result = TranscriptionResult(
                text=result["text"].strip(),
                confidence=confidence,
                language=result.get("language", "unknown"),
                processing_time=processing_time
            )
            
            logger.info(
                f"Transcription completed in {processing_time:.3f}s: "
                f"'{transcription_result.text[:50]}...'"
            )
            
            return transcription_result
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise
    
    def _prepare_audio(self, audio_data: bytes) -> np.ndarray:
        """
        Prepare audio data for Whisper processing.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Normalized numpy array
        """
        # Convert bytes to numpy array
        # Assuming 16-bit PCM audio at sample rate defined in settings
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Convert to float32 and normalize to [-1, 1]
        audio_array = audio_array.astype(np.float32) / 32768.0
        
        # Ensure we have the right sample rate
        # Whisper expects 16kHz audio
        if len(audio_array) == 0:
            raise ValueError("Empty audio data received")
        
        return audio_array
    
    def _transcribe_sync(self, audio_array: np.ndarray) -> Dict[str, Any]:
        """
        Synchronous transcription method for thread pool execution.
        
        Args:
            audio_array: Prepared audio data
            
        Returns:
            Whisper transcription result
        """
        return self._model.transcribe(
            audio_array,
            language=None,  # Auto-detect language
            task="transcribe",
            verbose=False
        )
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """
        Calculate confidence score from Whisper result.
        
        Args:
            result: Whisper transcription result
            
        Returns:
            Confidence score between 0 and 1
        """
        # Whisper doesn't provide direct confidence scores
        # We can estimate based on segment scores if available
        segments = result.get("segments", [])
        
        if not segments:
            return 0.5  # Default moderate confidence
        
        # Average the no_speech_prob scores (lower is better)
        no_speech_probs = [
            segment.get("no_speech_prob", 0.5) 
            for segment in segments
        ]
        
        avg_no_speech_prob = sum(no_speech_probs) / len(no_speech_probs)
        
        # Convert to confidence (higher is better)
        confidence = 1.0 - avg_no_speech_prob
        
        return max(0.0, min(1.0, confidence))
    
    async def is_speech_detected(self, audio_data: bytes) -> bool:
        """
        Quick check if audio contains speech.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            True if speech is likely detected
        """
        try:
            # Simple energy-based voice activity detection
            audio_array = self._prepare_audio(audio_data)
            
            # Calculate RMS energy
            rms_energy = np.sqrt(np.mean(audio_array ** 2))

            # Threshold for speech detection (tunable)
            speech_threshold = 0.01

            return bool(rms_energy > speech_threshold)
            
        except Exception as e:
            logger.warning(f"Voice activity detection failed: {str(e)}")
            return True  # Assume speech if detection fails
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if (
            self._model
            and torch is not None
            and getattr(torch, "cuda", None)
            and torch.cuda.is_available()
        ):
            torch.cuda.empty_cache()

        self._model = None
        logger.info("Whisper STT resources cleaned up")
