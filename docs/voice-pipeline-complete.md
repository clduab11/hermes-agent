# HERMES Voice Pipeline Setup Guide

## 🎙️ Complete Voice Pipeline Implementation

The HERMES voice pipeline has been successfully implemented with Whisper STT + Kokoro TTS integration. This guide covers the complete setup and usage.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install fastapi uvicorn pydantic pydantic-settings python-multipart openai openai-whisper requests numpy torch torchaudio python-json-logger python-dotenv httpx
```

### 2. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start Mock TTS Server (for development)
```bash
python mock_tts_server.py
```
This starts the mock Kokoro TTS server on http://localhost:8001

### 4. Test the Voice Pipeline
```bash
python quick_demo.py
```

### 5. Start the Main Server
```bash
python -m hermes.main
```
Server available at: http://localhost:8000

## 🎯 Voice Pipeline Components

### Speech-to-Text (STT)
- **Engine**: OpenAI Whisper
- **Model**: Base model (configurable)
- **Features**: 
  - Confidence scoring
  - Language detection
  - Audio preprocessing

### Text-to-Speech (TTS)
- **Engine**: Kokoro TTS (with mock server for demo)
- **Features**:
  - Multiple voice options
  - Adjustable sample rates
  - Legal disclaimer injection
  - WAV format output

### LLM Integration
- **Engine**: OpenAI GPT-4
- **Features**:
  - Legal-specific system prompts
  - Prohibited content detection
  - Confidence-based human transfer
  - Voice-optimized responses

## 🔧 Configuration Options

### Environment Variables (.env)
```bash
# OpenAI Configuration (Required for LLM)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Whisper STT Configuration
WHISPER_MODEL=base
WHISPER_DEVICE=cpu

# Kokoro TTS Configuration
KOKORO_API_URL=http://localhost:8001
KOKORO_VOICE=af_sarah

# Audio Configuration
SAMPLE_RATE=16000
CHUNK_SIZE=1024
MAX_AUDIO_LENGTH_SECONDS=30
RESPONSE_TIMEOUT_SECONDS=0.1

# Legal Compliance
CONFIDENCE_THRESHOLD=0.85
ENABLE_DISCLAIMERS=true
AUDIT_LOGGING=true
```

## 🎮 Demo Interface

Access the interactive voice demo at: http://localhost:8000/

Features:
- Real-time WebSocket communication
- Voice recording and playback
- Live transcription display
- Audio response streaming

## 🔌 API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### System Status
```bash
curl http://localhost:8000/status
```

### Test TTS
```bash
curl -X POST http://localhost:8000/test/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from HERMES"}'
```

### Available Voices
```bash
curl http://localhost:8000/voices
```

## 🌐 WebSocket Communication

Connect to: `ws://localhost:8000/voice`

### Message Types

#### Audio Input
```javascript
// Send binary audio data
websocket.send(audioBuffer);
```

#### Text Commands
```javascript
// Send JSON commands
websocket.send(JSON.stringify({
  "type": "start_session",
  "data": {}
}));
```

## 🛡️ Legal Compliance Features

- **Prohibited phrase filtering**
- **Automatic legal disclaimers**
- **Confidence threshold monitoring**
- **Attorney-client privilege protection**
- **Audit logging**

## 🧪 Testing

### Component Testing
```bash
# Test TTS only
python test_tts.py

# Test complete pipeline
python quick_demo.py

# Test with OpenAI (requires API key)
python setup_demo.py
```

### Production Deployment
```bash
# Start complete system
python complete_demo.py
```

## 📁 File Structure
```
hermes/
├── __init__.py              # Package initialization
├── config.py               # Configuration management
├── speech_to_text.py       # Whisper STT integration
├── text_to_speech.py       # Kokoro TTS integration
├── voice_pipeline.py       # Core pipeline orchestration
├── websocket_handler.py    # WebSocket communication
└── main.py                 # FastAPI application

static/demo.html            # Interactive demo interface
mock_tts_server.py          # Development TTS server
test_tts.py                 # TTS component test
quick_demo.py               # Pipeline demonstration
complete_demo.py            # Full system demo
requirements.txt            # Python dependencies
.env.example                # Configuration template
```

## 🎉 What's Working

✅ **Complete STT → LLM → TTS Pipeline**  
✅ **WebSocket Real-time Communication**  
✅ **Mock TTS Server for Development**  
✅ **Legal Compliance Features**  
✅ **Interactive Web Demo**  
✅ **Production-ready FastAPI Server**  
✅ **Comprehensive Error Handling**  
✅ **Voice Activity Detection**  
✅ **Multi-voice TTS Support**  

## 🔧 Production Setup

For production deployment with real Kokoro TTS:
1. Replace `KOKORO_API_URL` with actual Kokoro server
2. Set valid `OPENAI_API_KEY` for LLM functionality
3. Configure appropriate audio settings
4. Enable SSL/TLS for WebSocket security
5. Set up logging and monitoring

The voice pipeline is now complete and ready for legal assistant applications!