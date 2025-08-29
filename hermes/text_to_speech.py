"""
Text-to-Speech implementation using Kokoro TTS.
"""
import asyncio
import logging
import time
from typing import Optional, Dict, Any

import httpx
from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)


class SynthesisResult(BaseModel):
    """Result of text-to-speech synthesis."""
    audio_data: bytes
    sample_rate: int
    duration: float
    processing_time: float


class KokoroTTS:
    """Text-to-speech processor using Kokoro TTS API."""
    
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._api_url = settings.kokoro_api_url
        self._voice = settings.kokoro_voice
        
    async def initialize(self) -> None:
        """Initialize the Kokoro TTS client."""
        logger.info(f"Initializing Kokoro TTS client: {self._api_url}")
        
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
        
        # Test connection
        try:
            await self._health_check()
            logger.info("Kokoro TTS client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Kokoro TTS: {str(e)}")
            raise
    
    async def _health_check(self) -> None:
        """Check if Kokoro TTS API is available."""
        if not self._client:
            raise RuntimeError("Client not initialized")
        
        try:
            response = await self._client.get(f"{self._api_url}/")
            response.raise_for_status()
        except httpx.RequestError as e:
            raise ConnectionError(f"Cannot connect to Kokoro TTS API: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise ConnectionError(f"Kokoro TTS API returned error: {e.response.status_code}")
    
    async def synthesize_text(self, text: str, voice: Optional[str] = None) -> SynthesisResult:
        """
        Synthesize text to speech audio.
        
        Args:
            text: Text to synthesize
            voice: Voice to use (optional, defaults to configured voice)
            
        Returns:
            SynthesisResult with audio data and metadata
        """
        if not self._client:
            raise RuntimeError("Kokoro TTS client not initialized. Call initialize() first.")
        
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        start_time = time.time()
        
        # Prepare request
        voice_to_use = voice or self._voice
        
        # Add legal disclaimer if enabled
        if settings.enable_disclaimers:
            text = self._add_legal_disclaimer(text)
        
        try:
            # Make TTS request
            response = await self._make_tts_request(text, voice_to_use)
            
            processing_time = time.time() - start_time
            
            # Extract audio data
            audio_data = response.content
            
            # Get metadata from response headers
            sample_rate = int(response.headers.get("X-Sample-Rate", settings.sample_rate))
            duration = float(response.headers.get("X-Duration", "0.0"))
            
            synthesis_result = SynthesisResult(
                audio_data=audio_data,
                sample_rate=sample_rate,
                duration=duration,
                processing_time=processing_time
            )
            
            logger.info(
                f"TTS synthesis completed in {processing_time:.3f}s: "
                f"{len(text)} chars -> {len(audio_data)} bytes"
            )
            
            return synthesis_result
            
        except Exception as e:
            logger.error(f"TTS synthesis failed: {str(e)}")
            raise
    
    async def _make_tts_request(self, text: str, voice: str) -> httpx.Response:
        """
        Make TTS request to Kokoro API.
        
        Args:
            text: Text to synthesize
            voice: Voice to use
            
        Returns:
            HTTP response with audio data
        """
        payload = {
            "text": text,
            "voice": voice,
            "sample_rate": settings.sample_rate,
            "format": "wav"
        }
        
        try:
            response = await self._client.post(
                f"{self._api_url}/synthesize",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "audio/wav"
                }
            )
            
            response.raise_for_status()
            return response
            
        except httpx.RequestError as e:
            raise ConnectionError(f"TTS request failed: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise ValueError(f"TTS API error {e.response.status_code}: {e.response.text}")
    
    def _add_legal_disclaimer(self, text: str) -> str:
        """
        Add legal disclaimer to text if appropriate.
        
        Args:
            text: Original text
            
        Returns:
            Text with disclaimer appended if needed
        """
        # Check if text contains legal advice indicators
        legal_keywords = [
            "advise", "recommend", "should", "must", "legal", "law", 
            "court", "attorney", "lawyer", "litigation", "contract"
        ]
        
        text_lower = text.lower()
        contains_legal_content = any(keyword in text_lower for keyword in legal_keywords)
        
        if contains_legal_content:
            disclaimer = (
                " Please note that this information is for general guidance only "
                "and does not constitute legal advice. Consult with a qualified "
                "attorney for specific legal matters."
            )
            return text + disclaimer
        
        return text
    
    async def get_available_voices(self) -> Dict[str, Any]:
        """
        Get list of available voices from Kokoro TTS.
        
        Returns:
            Dictionary of available voices and their properties
        """
        if not self._client:
            raise RuntimeError("Client not initialized")
        
        try:
            response = await self._client.get(f"{self._api_url}/voices")
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get available voices: {str(e)}")
            raise
    
    async def estimate_duration(self, text: str) -> float:
        """
        Estimate audio duration for given text.
        
        Args:
            text: Text to estimate duration for
            
        Returns:
            Estimated duration in seconds
        """
        # Rough estimation: ~150 words per minute average speaking rate
        # Average 5 characters per word
        words = len(text) / 5
        duration = (words / 150) * 60
        
        return max(0.5, duration)  # Minimum 0.5 seconds
    
    async def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for better TTS synthesis.
        
        Args:
            text: Raw text
            
        Returns:
            Processed text optimized for speech synthesis
        """
        # Remove or replace problematic characters
        text = text.replace("&", "and")
        text = text.replace("@", "at")
        text = text.replace("#", "number")
        text = text.replace("$", "dollars")
        text = text.replace("%", "percent")
        
        # Expand common abbreviations
        abbreviations = {
            "Dr.": "Doctor",
            "Mr.": "Mister", 
            "Mrs.": "Missus",
            "Ms.": "Miss",
            "St.": "Street",
            "Ave.": "Avenue",
            "Inc.": "Incorporated",
            "LLC": "Limited Liability Company",
            "Corp.": "Corporation"
        }
        
        for abbrev, expansion in abbreviations.items():
            text = text.replace(abbrev, expansion)
        
        # Ensure proper sentence endings for natural pauses
        if text and not text.endswith(('.', '!', '?')):
            text += '.'
        
        return text.strip()
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
        
        logger.info("Kokoro TTS resources cleaned up")