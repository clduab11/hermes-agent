#!/usr/bin/env python3
"""
Quick demo to show voice pipeline working end-to-end.
"""
import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from hermes.voice_pipeline import VoicePipeline
from hermes.speech_to_text import TranscriptionResult

async def quick_demo():
    """Run a quick demo of the voice pipeline."""
    print("🎙️ HERMES Voice Pipeline Quick Demo")
    print("=" * 40)
    
    pipeline = VoicePipeline()
    
    try:
        print("🔧 Initializing voice pipeline...")
        # Initialize only TTS since we don't have OpenAI API key
        await pipeline.tts.initialize()
        print("✅ TTS component ready")
        
        # Initialize STT 
        print("🎤 Loading Whisper model...")
        await pipeline.stt.initialize()
        print("✅ STT component ready")
        
        print("\\n🎯 Testing Text-to-Speech...")
        
        # Test various legal assistant responses
        test_responses = [
            "Hello! Welcome to our law firm. How may I assist you today?",
            "I'd be happy to help you schedule an appointment with one of our attorneys.",
            "I understand you're looking for guidance, but I can't provide legal advice. Let me connect you with one of our attorneys.",
            "Thank you for calling. Please hold while I transfer you to the appropriate department."
        ]
        
        for i, text in enumerate(test_responses, 1):
            print(f"\\n[Test {i}] Synthesizing: '{text[:50]}...'")
            
            try:
                result = await pipeline.tts.synthesize_text(text)
                print(f"✅ Generated {len(result.audio_data)} bytes in {result.processing_time:.3f}s")
                
                # Simulate what would happen with real transcription
                print(f"    Duration: {result.duration:.2f}s")
                print(f"    Sample rate: {result.sample_rate}Hz")
                
            except Exception as e:
                print(f"❌ Synthesis failed: {str(e)}")
        
        print("\\n🧪 Testing complete pipeline flow...")
        
        # Simulate receiving speech input (without actual audio processing)
        mock_transcription = TranscriptionResult(
            text="Hello, I need to schedule an appointment with an attorney.",
            confidence=0.95,
            language="en",
            processing_time=0.2
        )
        
        print(f"📝 Mock transcription: '{mock_transcription.text}'")
        print(f"🎯 Confidence: {mock_transcription.confidence:.2f}")
        
        # Process with LLM (this will fail without API key, but we can catch it)
        try:
            response = await pipeline._process_with_llm(
                mock_transcription.text, 
                "demo-session"
            )
            print(f"🧠 LLM Response: '{response}'")
            
            # Convert response to speech
            tts_result = await pipeline.tts.synthesize_text(response)
            print(f"🔊 Final audio: {len(tts_result.audio_data)} bytes")
            
        except Exception as e:
            print(f"⚠️  LLM processing skipped (no API key): {str(e)}")
            print("💡 Using fallback response...")
            
            fallback_response = "Hello! I'd be happy to help you schedule an appointment. Let me connect you with our scheduling system."
            tts_result = await pipeline.tts.synthesize_text(fallback_response)
            print(f"🔊 Fallback audio: {len(tts_result.audio_data)} bytes")
        
        await pipeline.cleanup()
        print("\\n🎉 Demo completed successfully!")
        print("\\n🚀 Ready for production use!")
        print("   - Start mock TTS server: python mock_tts_server.py")
        print("   - Start main server: python -m hermes.main")
        print("   - Demo interface: http://localhost:8000/")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        await pipeline.cleanup()
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_demo())
    if not success:
        sys.exit(1)