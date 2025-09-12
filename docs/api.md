


# HERMES API Documentation

The HERMES AI Voice Agent System provides a comprehensive REST API and WebSocket interface for real-time voice interactions with legal AI capabilities.

## Base URL
- Development: `http://localhost:8000`
- Production: `https://your-hermes-deployment.run.app`

## Authentication
All API endpoints require JWT authentication except for health checks and public documentation.

```bash
# Get access token
curl -X POST /auth/token \
  -H "Content-Type: application/json" \
  -d '{"subject": "user@example.com", "tenant_id": "your-tenant-id"}'
```
        


## Health Check
Check system health and component status.

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "HERMES AI Voice Agent",
  "version": "1.0.0",
  "active_connections": 0
}
```

## System Status
Get detailed system status including MCP orchestration.

```http
GET /status
```

**Response:**
```json
{
  "service": "HERMES AI Voice Agent",
  "status": "operational",
  "components": {
    "voice_pipeline": "initialized",
    "mcp_orchestrator": "active",
    "database_optimizer": "active",
    "knowledge_integrator": "active"
  },
  "mcp_orchestration": {...},
  "database_performance": {...}
}
```

## Voice Synthesis Test
Test text-to-speech synthesis.

```http
POST /test/synthesize
Content-Type: application/json

{
  "text": "Hello, this is HERMES voice assistant.",
  "voice": "af_sarah"
}
```

## Available Voices
Get list of available TTS voices.

```http
GET /voices
```
        


## Execute Strategic Task
Execute a specific MCP strategic task.

```http
POST /mcp/execute/{task_name}
Content-Type: application/json

{
  "tenant_id": "your-tenant-id",
  "parameters": {}
}
```

**Available Tasks:**
- `database_optimization` - Optimize database with caching
- `knowledge_integration` - Create knowledge graph
- `ui_validation` - Run automated UI tests
- `documentation_generation` - Generate documentation
- `search_intelligence` - Setup multi-provider search
- `reasoning_enhancement` - Add decision trees

## MCP System Status
Get MCP orchestration status.

```http
GET /mcp/status
```

## Comprehensive Orchestration
Execute all strategic tasks simultaneously.

```http
POST /mcp/orchestrate
```
        


## Search Legal Knowledge
Search across legal knowledge sources.

```http
GET /knowledge/search?query=contract+law&tenant_id=your-tenant&limit=10
```

## Get Conversation Context
Get contextual knowledge for a conversation.

```http
GET /knowledge/context/{conversation_id}?tenant_id=your-tenant
```

## Knowledge Insights
Get knowledge usage insights for optimization.

```http
GET /knowledge/insights/{tenant_id}
```
        


## Voice WebSocket Connection
Real-time voice interaction via WebSocket.

```javascript
const ws = new WebSocket('ws://localhost:8000/voice');

ws.onopen = function(event) {
    console.log('Connected to HERMES voice interface');
};

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    console.log('Received:', message);
};

// Send audio data
ws.send(JSON.stringify({
    type: 'audio_data',
    data: base64AudioData
}));

// Send text message
ws.send(JSON.stringify({
    type: 'text_message', 
    text: 'Hello HERMES'
}));
```

## WebSocket Message Types
- `audio_data` - Send audio for voice recognition
- `text_message` - Send text message
- `start_recording` - Start audio recording
- `stop_recording` - Stop audio recording
- `get_status` - Get connection status
        