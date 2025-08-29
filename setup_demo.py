#!/usr/bin/env python3
"""
HERMES Voice Agent Setup and Demo Script
Copyright (c) 2024 Parallax Analytics LLC. All rights reserved.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from hermes.config import settings
from hermes.voice_pipeline import VoicePipeline


async def setup_demo():
    """Setup and run a basic demo of the HERMES voice pipeline."""
    print("🏛️ HERMES AI Voice Agent System Demo")
    print("=" * 50)
    
    # Check if OpenAI API key is configured
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        print("❌ OpenAI API key not configured!")
        print("Please set OPENAI_API_KEY in your .env file")
        return False
    
    print("✅ Configuration loaded")
    print(f"   - Whisper Model: {settings.whisper_model}")
    print(f"   - TTS API: {settings.kokoro_api_url}")
    print(f"   - OpenAI Model: {settings.openai_model}")
    print()
    
    # Initialize voice pipeline
    print("🎙️ Initializing voice pipeline...")
    try:
        pipeline = VoicePipeline()
        await pipeline.initialize()
        print("✅ Voice pipeline initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize voice pipeline: {str(e)}")
        print("\nCommon issues:")
        print("- Ensure OpenAI API key is valid")
        print("- Check if Kokoro TTS server is running")
        print("- Verify network connectivity")
        return False
    
    print()
    print("🎯 Voice Pipeline Demo")
    print("-" * 30)
    
    # Demo text processing (simulating transcribed audio)
    demo_texts = [
        "Hello, I need to schedule an appointment with an attorney.",
        "What are your office hours?",
        "Can you help me with my divorce case?",  # This should trigger compliance response
        "I would like to speak with someone about estate planning."
    ]
    
    for i, text in enumerate(demo_texts, 1):
        print(f"\n[Demo {i}] Simulating transcribed input:")
        print(f"Input: '{text}'")
        
        try:
            # Simulate a complete voice interaction with dummy audio
            dummy_audio = b'\x00' * 1024  # Dummy audio data
            
            interaction = await pipeline.process_voice_interaction(
                session_id=f"demo-{i}",
                audio_data=dummy_audio
            )
            
            # Since we're using dummy audio, manually set transcription for demo
            if not interaction.transcription:
                from hermes.speech_to_text import TranscriptionResult
                interaction.transcription = TranscriptionResult(
                    text=text,
                    confidence=0.95,
                    language="en",
                    processing_time=0.1
                )
            
            # Process with LLM
            response = await pipeline._process_with_llm(text, f"demo-{i}")
            
            print(f"Response: '{response}'")
            print(f"Processing time: {interaction.total_processing_time:.3f}s")
            
        except Exception as e:
            print(f"❌ Error processing demo {i}: {str(e)}")
    
    # Cleanup
    await pipeline.cleanup()
    print("\n🎉 Demo completed successfully!")
    print("\nTo start the full web server, run:")
    print("python -m hermes.main")
    
    return True


async def check_dependencies():
    """Check if all required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    missing_deps = []
    
    try:
        import whisper
        print("✅ OpenAI Whisper installed")
    except ImportError:
        missing_deps.append("openai-whisper")
    
    try:
        import torch
        print("✅ PyTorch installed")
    except ImportError:
        missing_deps.append("torch")
    
    try:
        import openai
        print("✅ OpenAI Python library installed")
    except ImportError:
        missing_deps.append("openai")
    
    try:
        import fastapi
        print("✅ FastAPI installed")
    except ImportError:
        missing_deps.append("fastapi")
    
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All core dependencies installed")
    return True


def main():
    """Main setup function."""
    print("🏛️ HERMES AI Voice Agent System")
    print("High-performance Enterprise Reception & Matter Engagement System")
    print("Copyright (c) 2024 Parallax Analytics LLC")
    print("=" * 60)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  No .env file found. Creating from template...")
        example_env = Path(".env.example")
        if example_env.exists():
            import shutil
            shutil.copy(example_env, env_file)
            print(f"✅ Created .env file from template")
            print("📝 Please edit .env and add your API keys before continuing")
            return
        else:
            print("❌ No .env.example template found")
            return
    
    # Run async setup
    try:
        result = asyncio.run(check_dependencies())
        if result:
            asyncio.run(setup_demo())
    except KeyboardInterrupt:
        print("\n\n👋 Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")


if __name__ == "__main__":
    main()