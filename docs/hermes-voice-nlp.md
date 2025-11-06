# HERMES Voice & NLP Architecture

## Overview

This document describes the HERMES voice and NLP architecture, focusing on the newly implemented Kokoro TTS integration and semantic document ingestion pipeline.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Kokoro TTS Integration](#kokoro-tts-integration)
3. [Semantic Document Ingestion](#semantic-document-ingestion)
4. [Clio Integration](#clio-integration)
5. [Configuration](#configuration)
6. [Usage Examples](#usage-examples)
7. [Performance Considerations](#performance-considerations)
8. [Security](#security)

## Architecture Overview

HERMES uses a modular, plugin-based architecture for voice synthesis and document processing:

```
┌─────────────────────────────────────────────────────────────┐
│                     HERMES Voice Pipeline                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │              │  │              │  │              │      │
│  │   Speech     │─▶│   Language   │─▶│     TTS      │      │
│  │ Recognition  │  │    Model     │  │   Engine     │      │
│  │  (Whisper)   │  │   (OpenAI)   │  │  (Kokoro)    │      │
│  │              │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Semantic Document Processing                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │              │  │              │  │              │      │
│  │   Document   │─▶│  Embeddings  │─▶│    Vector    │      │
│  │   Ingestion  │  │  Generator   │  │    Store     │      │
│  │  (Chunking)  │  │   (OpenAI)   │  │  (pgvector)  │      │
│  │              │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│                         │                                     │
│                         ▼                                     │
│                  ┌──────────────┐                            │
│                  │              │                            │
│                  │     Clio     │                            │
│                  │  Integration │                            │
│                  │              │                            │
│                  └──────────────┘                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Kokoro TTS Integration

### Features

- **Multilingual Support**: English (en-US, en-GB), Spanish (es-ES, es-MX), French, German, Italian, Portuguese, Japanese, Korean, Chinese
- **Low Latency**: Target <500ms synthesis time for real-time conversations
- **Multiple Voices**: Professional and friendly voices for each locale
- **Dual Modes**: API mode (hosted) or local mode (self-hosted)
- **Automatic Fallback**: Falls back to alternative backend if Kokoro unavailable

### Architecture

The TTS module uses an abstract interface pattern:

```python
from hermes.tts import get_tts_engine, SynthesisRequest

# Get TTS engine (config-driven)
tts = get_tts_engine()
await tts.initialize()

# Synthesize speech
request = SynthesisRequest(
    text="Hello, welcome to our law firm!",
    locale="en-US",
    voice_id="kokoro-en-us-female-1"
)

result = await tts.synthesize(request)
# result.audio_data contains the MP3 audio
# result.synthesis_time_ms shows latency
# result.is_low_latency indicates if <500ms
```

### Backend Selection

Configure via environment variables or config file:

```yaml
tts:
  backend: kokoro  # Primary backend
  fallback_backend: openai  # Fallback if Kokoro fails
  
  kokoro:
    api_url: https://api.kokoro-tts.example.com
    api_key: your-api-key
    # OR for local mode:
    # model_path: /path/to/models
    # device: cuda
```

### Voice Selection

Available voices per locale:

| Locale | Voice ID | Gender | Style |
|--------|----------|--------|-------|
| en-US | kokoro-en-us-female-1 | Female | Professional |
| en-US | kokoro-en-us-female-2 | Female | Friendly |
| en-US | kokoro-en-us-male-1 | Male | Professional |
| en-US | kokoro-en-us-male-2 | Male | Friendly |
| es-ES | kokoro-es-es-female-1 | Female | Professional |
| es-ES | kokoro-es-es-male-1 | Male | Professional |

### Performance Monitoring

The TTS system tracks synthesis latency:

```python
result = await tts.synthesize(request)

print(f"Synthesis time: {result.synthesis_time_ms}ms")
print(f"Low latency: {result.is_low_latency}")  # True if <500ms
print(f"Audio duration: {result.duration_ms}ms")

# Metadata includes:
# - text_length
# - word_count
# - speed multiplier
# - mode (api or local)
```

## Semantic Document Ingestion

### Pipeline Overview

The document ingestion pipeline processes legal documents (PDF, DOCX, TXT) into searchable embeddings:

1. **Document Upload** → 2. **MIME Detection** → 3. **Text Extraction**
4. **Chunking** → 5. **Embedding** → 6. **Vector Storage**

### Chunking Strategy

- **Token-based chunking**: 800 tokens per chunk
- **Overlap**: 120 tokens between chunks
- **Metadata preserved**: filename, source, practice area, client/matter IDs

### Embedding Generation

Uses OpenAI's `text-embedding-3-large` model (3072 dimensions):

```python
from hermes.nlp.embedding import get_embedder

embedder = await get_embedder()

# Generate embeddings for chunks
embeddings = await embedder.embed_chunks(text_chunks)
```

### Vector Storage (pgvector)

Embeddings stored in Supabase with pgvector extension:

```sql
CREATE TABLE embeddings_v1 (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    embedding VECTOR(3072),
    metadata JSONB,
    practice_area TEXT,
    client_id UUID,
    matter_id UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON embeddings_v1 USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### Retrieval

Semantic search with filters:

```python
POST /v1/retrieve
{
    "query": "personal injury case with vehicle accident",
    "top_k": 10,
    "filters": {
        "practice_area": "Personal Injury",
        "client_id": "uuid-here"
    }
}
```

Response:

```json
{
    "results": [
        {
            "content": "...",
            "score": 0.92,
            "metadata": {...}
        }
    ]
}
```

## Clio Integration

### Semantic Field Population

The Clio adapter maps extracted entities to Clio objects:

```python
from hermes.integrations.clio.adapter import ClioAdapter

adapter = ClioAdapter(dry_run=True)

# Extract entities from conversation/document
entities = {
    "client_name": "John Doe",
    "client_email": "john@example.com",
    "case_type": "Personal Injury",
    "description": "Vehicle accident on Main St..."
}

# Map to Clio objects
clio_records = await adapter.create_records(entities)
# In dry-run mode, returns what would be created without actually creating
```

### Field Mapping

Configure field mappings in `config.yaml`:

```yaml
clio:
  field_mapping:
    contact:
      - source: client_name
        target: name
      - source: client_email
        target: email_addresses[0].address
    matter:
      - source: case_type
        target: practice_area
      - source: description
        target: description
```

### Dry-Run Mode

Test integrations safely:

```python
# Dry-run mode (default for testing)
adapter = ClioAdapter(dry_run=True)
result = await adapter.create_contact(data)
# Returns: {"would_create": {...}, "validation": "passed"}

# Live mode (production)
adapter = ClioAdapter(dry_run=False)
result = await adapter.create_contact(data)
# Returns: {"id": "contact-123", "status": "created"}
```

## Configuration

### Environment Variables

```bash
# TTS
TTS_BACKEND=kokoro
TTS_FALLBACK_BACKEND=openai
KOKORO_API_URL=https://api.kokoro-tts.example.com
KOKORO_API_KEY=your-api-key

# Embeddings
OPENAI_API_KEY=your-openai-key
EMBEDDING_MODEL=text-embedding-3-large

# Vector Store
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_ROLE_KEY=your-service-key

# Clio
CLIO_API_KEY=your-clio-key
CLIO_ENABLE_SEMANTIC=true
CLIO_DRY_RUN=true
```

### YAML Configuration

See `config.yaml.example` for complete configuration structure.

## Usage Examples

### E2E Voice Workflow

```python
from hermes.tts import get_tts_engine, SynthesisRequest
from hermes.voice.multilang_support import get_multilang_processor

# Initialize components
tts = get_tts_engine()
await tts.initialize()

voice_processor = get_multilang_processor()

# Process incoming audio
transcription, _ = await voice_processor.process_audio_conversation(
    audio_data=client_audio_bytes
)

# Generate LLM response
llm_response = await generate_response(transcription.text)

# Synthesize voice response
synthesis_request = SynthesisRequest(
    text=llm_response,
    locale=transcription.language.value[2],  # Use detected language
    voice_id="kokoro-en-us-female-1"
)

result = await tts.synthesize(synthesis_request)

# Send audio back to client
await send_audio_to_client(result.audio_data)
```

### Document Ingestion Workflow

```python
from hermes.ingest import DocumentIngestor
from hermes.nlp.embedding import get_embedder
from hermes.store.vector import PGVectorStore

# Initialize components
ingestor = DocumentIngestor()
embedder = await get_embedder()
vector_store = PGVectorStore()

# Ingest document
doc_path = "path/to/legal-document.pdf"
chunks = await ingestor.ingest_file(
    doc_path,
    metadata={
        "practice_area": "Personal Injury",
        "client_id": "client-uuid",
        "matter_id": "matter-uuid"
    }
)

# Generate embeddings
embeddings = await embedder.embed_chunks([c.text for c in chunks])

# Store in vector database
await vector_store.upsert(chunks, embeddings)
```

### Semantic Retrieval

```python
from hermes.retrieval import SemanticRetriever

retriever = SemanticRetriever()

# Search for relevant content
results = await retriever.search(
    query="vehicle accident personal injury claim",
    top_k=5,
    filters={
        "practice_area": "Personal Injury"
    }
)

for result in results:
    print(f"Score: {result.score:.2f}")
    print(f"Content: {result.content}")
    print(f"Metadata: {result.metadata}")
```

## Performance Considerations

### TTS Optimization

1. **Latency**: Kokoro targets <500ms. Monitor `synthesis_time_ms`.
2. **Caching**: Enable for repeated phrases (greetings, etc.)
3. **Streaming**: Consider streaming TTS for long text
4. **Voice Selection**: Simpler voices may be faster

### Embedding Optimization

1. **Batch Processing**: Process multiple chunks in parallel
2. **Chunking**: Balance chunk size vs. semantic coherence
3. **Caching**: Cache embeddings for static documents
4. **Index Tuning**: Adjust pgvector index parameters for your data size

### Vector Search Optimization

1. **Index Type**: Use IVFFlat for <1M vectors, HNSW for >1M
2. **Index Parameters**: Tune `lists` and `probes` based on accuracy/speed tradeoff
3. **Filtering**: Apply metadata filters to reduce search space
4. **Approximate Search**: Use approximate nearest neighbor for speed

## Security

### TTS Security

- API keys stored in environment variables, never in code
- HTTPS required for API mode
- Rate limiting on synthesis endpoints
- Input validation on text length and content

### Document Ingestion Security

- Validate file types (MIME detection)
- Scan uploads for malware
- Encrypt documents at rest
- Access control on vector store
- Audit log all ingestion operations

### Clio Integration Security

- OAuth 2.0 for authentication
- Separate credentials per tenant
- Dry-run mode prevents accidental data creation
- Field-level validation before API calls
- Comprehensive error logging

## Troubleshooting

### TTS Issues

**Problem**: High latency (>500ms)
- Check network connectivity to API
- Try local mode instead of API mode
- Reduce text length
- Check system resources (CPU/RAM)

**Problem**: "Locale not supported"
- Verify locale is in SUPPORTED_LOCALES
- Use standard BCP 47 format (e.g., "en-US" not "en_us")
- Add new locale to VOICE_CONFIGS if needed

### Embedding Issues

**Problem**: Slow embedding generation
- Increase batch size
- Use GPU acceleration if available
- Consider smaller embedding model
- Check OpenAI API rate limits

**Problem**: Poor retrieval quality
- Increase chunk overlap
- Adjust chunk size (too small or too large)
- Tune similarity threshold
- Add metadata filters to narrow search

### Clio Integration Issues

**Problem**: Field mapping failures
- Check field mapping configuration
- Verify Clio field names in API docs
- Enable dry-run mode for testing
- Check Clio API response errors

**Problem**: Authentication failures
- Verify API key is valid
- Check OAuth token expiration
- Ensure proper scopes for API operations

## References

- [Kokoro TTS Documentation](https://kokoro-tts.example.com/docs)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [pgvector Extension](https://github.com/pgvector/pgvector)
- [Clio API Reference](https://docs.clio.com/)
- [Supabase Vector Storage](https://supabase.com/docs/guides/ai/vector-columns)

## License

Copyright © 2024 HERMES Development Team. All rights reserved.
