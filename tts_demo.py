#!/usr/bin/env python3
"""
Test the TTS component independently.
"""
import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from hermes.text_to_speech import KokoroTTS

async def test_tts():
    """Test the TTS component."""
    print("🔊 Testing TTS Component")
    print("=" * 30)
    
    tts = KokoroTTS()
    
    try:
        print("Initializing TTS...")
        await tts.initialize()
        print("✅ TTS initialized successfully")
        
        print("Testing synthesis...")
        result = await tts.synthesize_text("Hello, this is a test of the HERMES voice system.")
        print(f"✅ Synthesis successful: {len(result.audio_data)} bytes, {result.duration:.2f}s duration")
        
        print("Testing voices...")
        voices = await tts.get_available_voices()
        print(f"✅ Available voices: {len(voices.get('voices', []))} voices found")
        
        await tts.cleanup()
        print("✅ TTS test completed successfully")
        
    except Exception as e:
        print(f"❌ TTS test failed: {str(e)}")
        await tts.cleanup()
        return False
        
    return True

if __name__ == "__main__":
    success = asyncio.run(test_tts())
    if not success:
        sys.exit(1)
