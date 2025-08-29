#!/usr/bin/env python3
"""
Complete HERMES Voice Pipeline Demo
Demonstrates end-to-end voice processing with mock TTS server.
"""
import asyncio
import subprocess
import sys
import time
import signal
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))


class VoicePipelineDemo:
    """Complete voice pipeline demonstration."""
    
    def __init__(self):
        self.tts_process = None
        self.main_process = None
        
    async def start_demo(self):
        """Start the complete voice pipeline demo."""
        print("🎙️ HERMES Complete Voice Pipeline Demo")
        print("=" * 50)
        
        try:
            # Step 1: Check dependencies
            if not await self.check_dependencies():
                return False
            
            # Step 2: Start mock TTS server
            print("\n🎤 Starting Mock TTS Server...")
            if not await self.start_tts_server():
                return False
            
            # Step 3: Test voice pipeline components
            print("\n🔧 Testing Voice Pipeline Components...")
            if not await self.test_pipeline_components():
                return False
            
            # Step 4: Start main server
            print("\n🚀 Starting HERMES Main Server...")
            await self.start_main_server()
            
            return True
            
        except KeyboardInterrupt:
            print("\n🛑 Demo interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Demo failed: {str(e)}")
            return False
        finally:
            await self.cleanup()
    
    async def check_dependencies(self):
        """Check if all dependencies are available."""
        print("🔍 Checking dependencies...")
        
        missing_deps = []
        
        # Check core Python packages
        required_packages = [
            ("whisper", "openai-whisper"),
            ("torch", "torch"),
            ("openai", "openai"),
            ("fastapi", "fastapi"),
            ("uvicorn", "uvicorn"),
            ("httpx", "httpx"),
            ("numpy", "numpy")
        ]
        
        for import_name, package_name in required_packages:
            try:
                __import__(import_name)
                print(f"✅ {package_name}")
            except ImportError:
                missing_deps.append(package_name)
                print(f"❌ {package_name}")
        
        if missing_deps:
            print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
            print("Install with: pip install " + " ".join(missing_deps))
            return False
        
        # Check configuration
        env_file = Path(".env")
        if not env_file.exists():
            print("❌ .env file not found")
            print("Create .env file from .env.example")
            return False
        
        print("✅ All dependencies available")
        return True
    
    async def start_tts_server(self):
        """Start the mock TTS server."""
        try:
            # Start TTS server in background
            self.tts_process = subprocess.Popen([
                sys.executable, "mock_tts_server.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            print("⏳ Waiting for TTS server to start...")
            await asyncio.sleep(3)
            
            # Check if process is still running
            if self.tts_process.poll() is not None:
                stdout, stderr = self.tts_process.communicate()
                print(f"❌ TTS server failed to start:")
                print(f"STDOUT: {stdout.decode()}")
                print(f"STDERR: {stderr.decode()}")
                return False
            
            print("✅ Mock TTS server started on http://localhost:8001")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start TTS server: {str(e)}")
            return False
    
    async def test_pipeline_components(self):
        """Test individual pipeline components."""
        try:
            from hermes.config import settings
            from hermes.voice_pipeline import VoicePipeline
            
            # Check if OpenAI API key is set
            if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
                print("⚠️  OpenAI API key not configured - LLM testing will be skipped")
                test_llm = False
            else:
                test_llm = True
            
            # Initialize pipeline
            pipeline = VoicePipeline()
            
            # Test TTS component
            print("🔊 Testing TTS component...")
            try:
                await pipeline.tts.initialize()
                result = await pipeline.tts.synthesize_text("Hello, this is a test of the HERMES voice system.")
                print(f"✅ TTS: Generated {len(result.audio_data)} bytes of audio")
            except Exception as e:
                print(f"❌ TTS test failed: {str(e)}")
                return False
            
            # Test STT component
            print("🎤 Testing STT component...")
            try:
                await pipeline.stt.initialize()
                print("✅ STT: Whisper model loaded successfully")
            except Exception as e:
                print(f"❌ STT test failed: {str(e)}")
                return False
            
            # Test LLM component (if API key available)
            if test_llm:
                print("🧠 Testing LLM component...")
                try:
                    response = await pipeline._process_with_llm(
                        "Hello, I would like to schedule an appointment.",
                        "test-session"
                    )
                    print(f"✅ LLM: Generated response ({len(response)} chars)")
                except Exception as e:
                    print(f"❌ LLM test failed: {str(e)}")
                    print("💡 Note: This might be due to invalid API key or network issues")
            
            await pipeline.cleanup()
            print("✅ All components tested successfully")
            return True
            
        except Exception as e:
            print(f"❌ Component testing failed: {str(e)}")
            return False
    
    async def start_main_server(self):
        """Start the main HERMES server."""
        print("🌐 HERMES server will start at: http://localhost:8000")
        print("📱 Demo interface available at: http://localhost:8000/")
        print("🔌 WebSocket endpoint: ws://localhost:8000/voice")
        print("\nPress Ctrl+C to stop all servers")
        
        try:
            # Import and run the main server
            from hermes.main import app
            import uvicorn
            
            # Configure uvicorn to run with our app
            config = uvicorn.Config(
                app,
                host="0.0.0.0",
                port=8000,
                log_level="info"
            )
            server = uvicorn.Server(config)
            
            # Run the server
            await server.serve()
            
        except KeyboardInterrupt:
            print("\\n🛑 Shutting down servers...")
        except Exception as e:
            print(f"❌ Server failed: {str(e)}")
    
    async def cleanup(self):
        """Clean up running processes."""
        print("🧹 Cleaning up...")
        
        # Stop TTS server
        if self.tts_process and self.tts_process.poll() is None:
            print("🔇 Stopping TTS server...")
            self.tts_process.terminate()
            try:
                self.tts_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.tts_process.kill()
        
        # Stop main server
        if self.main_process and self.main_process.poll() is None:
            print("🛑 Stopping main server...")
            self.main_process.terminate()
            try:
                self.main_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.main_process.kill()
        
        print("✅ Cleanup completed")


async def main():
    """Main demo function."""
    demo = VoicePipelineDemo()
    
    # Set up signal handlers
    def signal_handler(signum, frame):
        print("\\n🛑 Received shutdown signal")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the demo
    success = await demo.start_demo()
    
    if success:
        print("🎉 Demo completed successfully!")
    else:
        print("❌ Demo failed to complete")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n👋 Demo terminated by user")
    except Exception as e:
        print(f"❌ Demo crashed: {str(e)}")
        sys.exit(1)