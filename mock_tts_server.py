#!/usr/bin/env python3
"""
Mock TTS Server for HERMES Voice Agent Demo
Simulates Kokoro TTS API responses for development and testing.
"""
import asyncio
import io
import json
import logging
import wave
from typing import Optional

import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mock Kokoro TTS Server", version="1.0.0")


def generate_mock_audio(
    text: str, voice: str = "af_sarah", sample_rate: int = 16000
) -> bytes:
    """
    Generate mock audio for text synthesis.
    Creates a simple sine wave pattern based on text length.
    """
    # Simple audio generation - sine wave pattern
    duration = max(0.5, min(len(text) * 0.1, 10.0))  # 0.1s per character, max 10s
    samples = int(sample_rate * duration)

    # Generate a pleasant sine wave pattern
    t = np.linspace(0, duration, samples, False)
    frequency = 440.0  # A4 note
    audio_signal = 0.3 * np.sin(2 * np.pi * frequency * t)

    # Add some variation to make it sound more natural
    audio_signal += 0.1 * np.sin(2 * np.pi * (frequency * 1.5) * t)
    audio_signal += 0.05 * np.sin(2 * np.pi * (frequency * 0.5) * t)

    # Convert to 16-bit PCM
    audio_data = (audio_signal * 32767).astype(np.int16)

    # Create WAV format
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())

    return wav_buffer.getvalue()


@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {"service": "Mock Kokoro TTS Server", "status": "ready", "version": "1.0.0"}


@app.get("/voices")
async def get_available_voices():
    """Get available TTS voices."""
    return {
        "voices": [
            {"id": "af_sarah", "name": "Sarah (Female)", "language": "en"},
            {"id": "am_michael", "name": "Michael (Male)", "language": "en"},
            {"id": "af_alice", "name": "Alice (Female)", "language": "en"},
            {"id": "am_david", "name": "David (Male)", "language": "en"},
        ]
    }


@app.post("/synthesize")
async def synthesize_text(request: dict):
    """
    Synthesize text to speech.

    Expected request format:
    {
        "text": "Text to synthesize",
        "voice": "af_sarah",
        "sample_rate": 16000
    }
    """
    try:
        text = request.get("text", "")
        voice = request.get("voice", "af_sarah")
        sample_rate = request.get("sample_rate", 16000)

        if not text.strip():
            raise HTTPException(status_code=400, detail="Text is required")

        logger.info(f"Synthesizing: '{text[:50]}...' with voice '{voice}'")

        # Simulate processing time
        await asyncio.sleep(0.1)

        # Generate mock audio
        audio_data = generate_mock_audio(text, voice, sample_rate)

        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "X-Duration": str(len(text) * 0.1),
                "X-Voice": voice,
                "X-Sample-Rate": str(sample_rate),
            },
        )

    except Exception as e:
        logger.error(f"Synthesis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@app.post("/synthesize-json")
async def synthesize_text_json(request: dict):
    """
    Synthesize text to speech with JSON response.
    Returns base64-encoded audio data.
    """
    try:
        text = request.get("text", "")
        voice = request.get("voice", "af_sarah")
        sample_rate = request.get("sample_rate", 16000)

        if not text.strip():
            raise HTTPException(status_code=400, detail="Text is required")

        logger.info(f"Synthesizing (JSON): '{text[:50]}...' with voice '{voice}'")

        # Simulate processing time
        await asyncio.sleep(0.1)

        # Generate mock audio
        audio_data = generate_mock_audio(text, voice, sample_rate)

        import base64

        audio_b64 = base64.b64encode(audio_data).decode("utf-8")

        return {
            "success": True,
            "audio_data": audio_b64,
            "duration": len(text) * 0.1,
            "voice": voice,
            "sample_rate": sample_rate,
            "format": "wav",
        }

    except Exception as e:
        logger.error(f"Synthesis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


if __name__ == "__main__":
    print("🎤 Starting Mock Kokoro TTS Server...")
    print("Server will be available at: http://localhost:8001")
    print("Use Ctrl+C to stop")

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
