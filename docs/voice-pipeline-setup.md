# HERMES Voice Pipeline Setup Guide

This guide covers the setup and configuration of the HERMES voice processing pipeline with Whisper STT and Kokoro TTS integration.

## 🎙️ Voice Pipeline Architecture

The HERMES voice pipeline implements a real-time speech processing system:

```
Audio Input → Whisper STT → OpenAI LLM → Kokoro TTS → Audio Output
     ↓              ↓            ↓           ↓           ↓
WebSocket → Transcription → Response → Synthesis → WebSocket
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/clduab11/Hermes-beta.git
cd Hermes-beta

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your API keys
```

### 2. Configuration

Configure your `.env` file with the required API keys:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional (for enhanced features)
KOKORO_API_URL=http://localhost:8001
WHISPER_MODEL=base
CONFIDENCE_THRESHOLD=0.85
```

### 3. Running the System

```bash
# Start the voice agent server
python -m hermes.main

# Or run the demo script
python setup_demo.py
```

## 🛠️ Component Configuration

### Whisper Speech-to-Text

The system uses OpenAI Whisper for speech recognition:

```python
# Configuration options
WHISPER_MODEL=base          # Models: tiny, base, small, medium, large
WHISPER_DEVICE=cpu          # Options: cpu, cuda
CONFIDENCE_THRESHOLD=0.85   # Minimum confidence for processing
```

Available Whisper models:
- `tiny`: Fastest, lower accuracy (~39 MB)
- `base`: Balanced speed/accuracy (~74 MB) **[Recommended]**
- `small`: Better accuracy (~244 MB)
- `medium`: High accuracy (~769 MB)
- `large`: Highest accuracy (~1550 MB)

### Kokoro Text-to-Speech

Configure the Kokoro TTS integration:

```python
# TTS Configuration
KOKORO_API_URL=http://localhost:8001    # TTS server URL
KOKORO_VOICE=af_sarah                   # Voice selection
SAMPLE_RATE=16000                       # Audio sample rate
```

### OpenAI LLM Integration

Configure the language model for response generation:

```python
# LLM Configuration
OPENAI_MODEL=gpt-4              # Model selection
RESPONSE_TIMEOUT_SECONDS=0.1    # Response time target
```

## 🌐 WebSocket API

### Connection

Connect to the voice WebSocket endpoint:

```javascript
const ws = new WebSocket('ws://localhost:8000/voice');
```

### Message Types

#### Client → Server

**Audio Data (Binary)**
```javascript
// Send audio as binary WebSocket message
ws.send(audioArrayBuffer);
```

**Control Messages (JSON)**
```javascript
// Start session
ws.send(JSON.stringify({
    type: "start_session"
}));

// End session
ws.send(JSON.stringify({
    type: "end_session"
}));
```

#### Server → Client

**Transcription Result**
```json
{
    "type": "transcription",
    "text": "Hello, I need to schedule an appointment",
    "confidence": 0.95,
    "language": "en"
}
```

**Assistant Response**
```json
{
    "type": "response", 
    "text": "I'd be happy to help you schedule an appointment...",
    "requires_human_transfer": false
}
```

**Audio Response**
```json
{
    "type": "audio_response",
    "size": 24576
}
// Followed by binary audio data
```

**Processing Metrics**
```json
{
    "type": "metrics",
    "processing_time": 0.85,
    "confidence_score": 0.92
}
```

## 🧪 Testing the Voice Pipeline

### 1. Demo Web Interface

Access the web demo at `http://localhost:8000/` after starting the server:

```bash
python -m hermes.main
# Open browser to http://localhost:8000
```

### 2. Command Line Demo

Run the setup demo script:

```bash
python setup_demo.py
```

### 3. API Testing

Test individual components:

```bash
# Health check
curl http://localhost:8000/health

# System status
curl http://localhost:8000/status

# Test TTS synthesis
curl -X POST http://localhost:8000/test/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from HERMES voice assistant"}'
```

## ⚡ Performance Optimization

### Audio Processing

```python
# Optimize for real-time performance
CHUNK_SIZE=1024                    # Audio chunk size
MAX_AUDIO_LENGTH_SECONDS=30        # Maximum input length
SAMPLE_RATE=16000                  # Standard telephony rate
```

### GPU Acceleration

Enable GPU acceleration for Whisper:

```python
# Use CUDA if available
WHISPER_DEVICE=cuda

# Install CUDA-enabled PyTorch
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Latency Optimization

```python
# Target ultra-low latency
RESPONSE_TIMEOUT_SECONDS=0.1       # 100ms target
WHISPER_MODEL=tiny                 # Fastest model
```

## 🔒 Legal Compliance Features

### Automatic Disclaimers

```python
# Enable legal disclaimers
ENABLE_DISCLAIMERS=true

# Example disclaimer injection
"This information is for general guidance only and does not constitute legal advice."
```

### Confidence Thresholds

```python
# Set confidence requirements
CONFIDENCE_THRESHOLD=0.85

# Low confidence triggers human transfer
```

### Prohibited Content Detection

The system automatically detects and handles:
- Requests for legal advice
- Case strategy discussions
- Confidential information requests

## 🛡️ Security Configuration

### Audio Data Protection

- Audio data is processed in memory only
- No persistent audio storage
- Automatic cleanup after processing

### API Security

```python
# Enable audit logging
AUDIT_LOGGING=true

# TLS configuration
# Use proper certificates in production
```

## 🚨 Troubleshooting

### Common Issues

**Whisper Model Loading Fails**
```bash
# Check available memory
free -h

# Use smaller model
WHISPER_MODEL=tiny
```

**OpenAI API Errors**
```bash
# Verify API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

**TTS Connection Errors**
```bash
# Check Kokoro TTS server
curl http://localhost:8001/health
```

**WebSocket Connection Issues**
```bash
# Check firewall settings
# Verify port 8000 is available
netstat -tulpn | grep 8000
```

### Debug Mode

Enable detailed logging:

```python
DEBUG=true
LOG_LEVEL=debug
```

## 📊 Monitoring and Metrics

### Health Monitoring

```bash
# System health
curl http://localhost:8000/health

# Detailed status
curl http://localhost:8000/status
```

### Performance Metrics

The system tracks:
- Processing latency per component
- Confidence scores
- Active WebSocket connections
- Error rates

### Logging

Structured logging for:
- Voice interactions
- System events
- Error tracking
- Performance metrics

## 🔧 Advanced Configuration

### Custom Voice Models

Integrate custom TTS voices:

```python
# Configure custom voice
KOKORO_VOICE=custom_legal_voice

# Add voice mapping in code
voice_mappings = {
    "legal_male": "af_alex",
    "legal_female": "af_sarah"
}
```

### Multi-Language Support

Configure language detection:

```python
# Enable auto-detection
WHISPER_LANGUAGE=auto

# Set specific language
WHISPER_LANGUAGE=en
```

### Production Deployment

```python
# Production settings
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000

# Use production-grade settings
WHISPER_MODEL=base
CONFIDENCE_THRESHOLD=0.90
```

## 📞 Integration Examples

### Twilio Phone Integration

```python
# Example Twilio WebSocket integration
# See docs/integrations/twilio.md
```

### SIP Protocol Integration

```python
# Example SIP server integration  
# See docs/integrations/sip.md
```

### Asterisk PBX Integration

```python
# Example Asterisk AGI integration
# See docs/integrations/asterisk.md
```

---

For additional support and advanced configuration options, refer to the complete documentation in the `docs/` directory.