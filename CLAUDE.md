# 🏛️ HERMES - Claude Code Guidelines

---

## 📋 Project Overview

**HERMES (High-performance Enterprise Reception & Matter Engagement System)** is a production-grade, 24/7 AI-powered voice agent designed specifically for law firms. This system handles client intake, matter management, CRM integration, and administrative workflows while maintaining attorney-client privilege and legal compliance.

### 🎯 Key Characteristics

- **🚨 Mission-Critical**: System downtime = lost clients for law firms
- **⚖️ Compliance-First**: HIPAA, GDPR, SOC 2, attorney-client privilege protection
- **⚡ Real-Time Voice**: <500ms latency required for natural conversations
- **🏢 Multi-Tenant**: Designed to serve multiple law firms with isolated data

---

## 🛠️ Technical Stack

### Core Technologies

| Component | Technology |
|-----------|------------|
| **Backend** | Python 3.11+, FastAPI (ASGI) |
| **Voice Pipeline** | Real-time bidirectional WebSockets, Whisper (STT), Kokoro FastAPI (TTS), VAD |
| **AI/ML** | OpenRouter API, Tree of Thought (ToT), Monte Carlo simulation, Mem0 |
| **Database** | Supabase (PostgreSQL), Redis |
| **Integrations** | Clio CRM (OAuth 2.0), LawPay, Zapier |
| **Automation** | Playwright |
| **Deployment** | Docker, Docker Compose, Gunicorn/Uvicorn |

### 🏗️ Architecture Pattern

- **🔧 Microservices**: Separate services for voice, API, workers, automation
- **📡 Event-Driven**: Message queues (Celery + Redis) for async tasks
- **🌐 API-First**: RESTful + WebSocket APIs with OpenAPI documentation
- **🔄 Stateless Application**: Session state in Redis, not in-memory

---

## 📝 Coding Standards

### 🐍 Python Code Quality (MANDATORY)

#### ✅ Good Example
```python
from typing import Optional, List
from datetime import datetime

async def create_matter(
    client_name: str,
    matter_type: str,
    jurisdiction: str,
    description: Optional[str] = None
) -> dict[str, any]:
    """
    Create a new legal matter in Clio CRM.
    
    Args:
        client_name: Full name of the client
        matter_type: Type of legal matter (e.g., 'Personal Injury', 'Divorce')
        jurisdiction: Legal jurisdiction (e.g., 'CA', 'NY')
        description: Optional description of the matter
        
    Returns:
        dict containing matter_id and creation status
        
    Raises:
        ClioAPIError: If Clio API request fails
        ValueError: If required fields are invalid
    """
    # Implementation here
    pass
```

#### ❌ Bad Example
```python
def create_matter(client, type, desc=None):
    # What does this return? What can go wrong? Who knows!
    pass
```

### 📏 Required Standards

- **🎨 PEP 8 Compliance**: Use `black` for formatting (line length 88), `flake8` for linting
- **🏷️ Type Hints Everywhere**: All function parameters and return types must have type hints
- **📚 Docstrings**: Google-style docstrings for all public functions, classes, and modules
- **⚡ Async/Await**: Use async/await for all I/O operations (network, database, file system)
- **🛡️ Error Handling**: Specific exceptions, never bare `except:`
- **📊 Logging**: Use structured logging (JSON format), not `print()` statements

### 🏷️ Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Functions & Variables | `snake_case` | `create_matter()`, `client_name` |
| Classes | `PascalCase` | `VoicePipelineManager` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRY_ATTEMPTS` |
| Private Methods | `_snake_case` | `_internal_method()` |

---

## 📁 Code Organization

```
hermes/
├── 🌐 api/              # FastAPI routes and endpoints
│   ├── v1/              # API version 1
│   │   ├── voice.py
│   │   ├── matters.py
│   │   └── integrations.py
│   └── dependencies.py  # Dependency injection
├── ⚙️ core/             # Core business logic
│   ├── voice_pipeline.py
│   ├── reasoning.py
│   └── knowledge_graph.py
├── 🔌 integrations/     # External service integrations
│   ├── clio.py
│   ├── lawpay.py
│   └── zapier.py
├── 📊 models/           # Pydantic models and schemas
├── 🔧 services/         # Business logic services
├── 🛠️ utils/           # Utility functions
├── 🧪 tests/           # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── 🚀 main.py          # Application entry point
```

> **📝 File Naming**: Lowercase with underscores (snake_case). Example: `voice_pipeline_manager.py`

---

## 🔒 Security & Compliance (NON-NEGOTIABLE)

### 🛡️ Data Protection Rules

#### ❌ No Secrets in Code
- **NEVER** hardcode API keys, passwords, or tokens
- ✅ Use environment variables or secret management systems
- ✅ Add `.env` to `.gitignore`

#### 🔐 Encryption Requirements
- All voice data encrypted in transit (TLS 1.3)
- Sensitive data encrypted at rest (AES-256)
- Database connections use SSL/TLS

#### ⚖️ Attorney-Client Privilege Protection
- Mark all client communications as privileged
- Implement secure deletion (overwrite, not just delete)
- Log all access to privileged data
- **NEVER** cache privileged conversations in unsecured locations

#### ✅ Input Validation
- Validate **ALL** user inputs (use Pydantic models)
- Prevent SQL injection (use parameterized queries)
- Sanitize data before external API calls
- Rate limit all endpoints

#### 📋 Audit Logging
- Log every API call with: user, timestamp, action, result
- Log every data access: who, what, when
- Logs must be immutable and tamper-evident
- Retain logs for 7 years (legal requirement)

### 🔍 Compliance Checklist for PRs

Before merging any PR that handles sensitive data, ensure:

- [ ] Data encrypted in transit and at rest
- [ ] No plain-text secrets in code
- [ ] Input validation implemented
- [ ] Audit logging added
- [ ] Error messages don't leak sensitive info
- [ ] GDPR deletion capability (if applicable)
- [ ] BAA/DPA terms respected (for HIPAA)

---

## 🎤 AI & Voice Pipeline Guidelines

### ⚡ Voice Latency Requirements

**🎯 Target**: <500ms from user speech end to AI response start

#### Optimization Strategies:
- Use streaming for both STT and TTS
- Start LLM generation before STT completion (with confidence threshold)
- Cache common responses
- Optimize prompts for brevity without sacrificing quality
- Use WebRTC instead of WebSocket for lower latency (if needed)

### 🌳 LLM Reasoning Best Practices

#### Tree of Thought (ToT) Implementation:
```python
# Generate multiple reasoning paths
paths = [
    reason_path_1(query),
    reason_path_2(query),
    reason_path_3(query)
]

# Self-evaluate each path
evaluations = [evaluate_reasoning(path) for path in paths]

# Select best path
best_path = select_best(paths, evaluations)

# Validate with MC simulation
confidence = monte_carlo_simulate(best_path, num_simulations=100)

if confidence > 0.8:
    return best_path.response
else:
    return fallback_response()
```

#### 📝 Prompt Engineering Standards:
1. **Context First**: Provide legal domain context before the query
2. **Few-Shot Examples**: Include 2-3 examples for complex tasks
3. **Explicit Constraints**: Clearly state what NOT to do (e.g., "Never provide legal advice")
4. **Output Format**: Specify desired response format (JSON, text, etc.)
5. **Error Handling**: Include fallback instructions for edge cases

### 🎯 Hallucination Prevention

| Method | Description |
|--------|-------------|
| **Fact-Checking** | Validate legal facts against knowledge graph |
| **Confidence Scoring** | Return confidence level with every response |
| **Human-in-Loop** | Flag low-confidence responses for human review |
| **Cite Sources** | Reference specific knowledge graph entries |
| **MC Simulation** | Use Monte Carlo to validate reasoning consistency |

---

## 🔌 Integration Guidelines

### 🏛️ Clio CRM Integration

#### OAuth 2.0 Flow:
1. User authorizes HERMES via Clio OAuth
2. Store access token + refresh token securely (encrypted)
3. Refresh tokens 5 minutes before expiry
4. Handle multi-tenant: separate tokens per law firm

#### API Best Practices:
- Respect Clio rate limits (throttle requests)
- Implement exponential backoff for retries
- Cache frequently accessed data (contacts, matter types)
- Graceful degradation if Clio is down (queue operations)

#### Data Mapping:
- Map HERMES intake data to Clio fields accurately
- Handle missing fields gracefully (use defaults)
- Validate data before sending to Clio (avoid API errors)

### 💳 LawPay Integration

#### Trust Accounting Compliance:
- **NEVER** mix trust and operating account funds
- Validate payment type before processing
- Log all payment attempts for audit trail
- Handle payment failures gracefully (notify client)

### ⚡ Zapier Integration

#### Webhook Design:
- Use standard event names (e.g., `matter.created`, `client.contacted`)
- Include all relevant data in payload (avoid requiring follow-up calls)
- Provide webhook signature for verification
- Document all webhook events in OpenAPI spec

---

## 🧪 Testing Requirements

### 🎯 Test Coverage Targets

| Test Type | Coverage Target |
|-----------|----------------|
| **Unit Tests** | 80%+ code coverage |
| **Integration Tests** | All API endpoints, all integrations |
| **E2E Tests** | Critical user flows (intake call → matter created) |
| **Load Tests** | 100+ concurrent voice sessions |
| **Security Tests** | OWASP Top 10, penetration testing |

### 🧪 Testing Patterns

#### Unit Test Example (pytest)
```python
import pytest
from hermes.core.reasoning import tree_of_thought_reason

@pytest.mark.asyncio
async def test_tot_reasoning_personal_injury():
    """Test ToT reasoning for personal injury matter classification."""
    query = "I was hit by a car while crossing the street..."
    result = await tree_of_thought_reason(query)
    
    assert result.matter_type == "Personal Injury"
    assert result.confidence > 0.8
    assert "negligence" in result.reasoning.lower()
```

#### Integration Test Example
```python
@pytest.mark.integration
async def test_clio_matter_creation():
    """Test end-to-end matter creation in Clio."""
    client_data = {...}
    matter = await clio_service.create_matter(client_data)
    
    assert matter.id is not None
    assert matter.status == "Open"
    # Cleanup
    await clio_service.delete_matter(matter.id)
```

### 📊 Test Data

- Use `pytest.fixtures` for test data
- **NEVER** use production data in tests
- Create realistic synthetic data for legal scenarios
- Include edge cases (empty fields, special characters, long text)

---

## ⚡ Performance Guidelines

### 🎯 Optimization Priorities

1. **🎤 Voice Latency**: Optimize this above all else (target <500ms)
2. **💾 Database Queries**: Use indexes, avoid N+1 queries
3. **🗄️ Caching**: Redis for session state, frequent lookups
4. **⚡ Async Operations**: All I/O must be async
5. **🔗 Connection Pooling**: Database and HTTP connections

### 📊 Monitoring Requirements

#### Required Metrics:
- Voice pipeline latency (p50, p95, p99)
- API response times
- Database query durations
- LLM token usage and cost
- Integration API success rates
- Error rates by endpoint
- Concurrent user count

#### 🚨 Alerting Thresholds:

| Metric | Warning | Critical |
|--------|---------|----------|
| Voice latency | >1s | >2s |
| Error rate | >1% | >5% |
| Integration API | Down | Down |

---

## 📚 Documentation Standards

### 💻 Code Documentation

```python
class VoicePipelineManager:
    """
    Manages the real-time voice pipeline for client conversations.
    
    This class handles the bidirectional streaming of audio between the client
    and the AI system, including speech-to-text (STT), LLM reasoning, and
    text-to-speech (TTS).
    
    Attributes:
        stt_client: OpenAI Whisper client for speech-to-text
        tts_client: Kokoro TTS client for text-to-speech
        llm_client: OpenRouter client for AI reasoning
        vad: Voice Activity Detection for turn-taking
        
    Example:
        >>> manager = VoicePipelineManager(...)
        >>> async for audio_chunk in manager.stream_conversation(websocket):
        ...     await websocket.send(audio_chunk)
    """
```

### 🌐 API Documentation

- Use OpenAPI 3.0 spec for all REST endpoints
- Document all WebSocket events and messages
- Include example requests and responses
- Document error codes and meanings
- Provide Postman collection for testing

### 📋 Changelog

Maintain a `CHANGELOG.md` with:
- Version number and date
- Added features
- Changed behavior
- Deprecated features
- Removed features
- Fixed bugs
- Security updates

> **Format**: [Keep a Changelog](https://keepachangelog.com/)

---

## 🔀 Git Workflow

### 🌿 Branch Naming

| Type | Format | Example |
|------|--------|---------|
| New features | `feature/short-description` | `feature/clio-oauth-integration` |
| Bug fixes | `bugfix/short-description` | `bugfix/token-refresh-race` |
| Urgent fixes | `hotfix/short-description` | `hotfix/voice-latency-spike` |
| Code refactoring | `refactor/short-description` | `refactor/voice-pipeline-cleanup` |
| Documentation | `docs/short-description` | `docs/api-examples` |

### 💬 Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Examples:

```
feat(voice): implement VAD for natural turn-taking

Added Voice Activity Detection using WebRTC VAD to detect when 
the user has finished speaking, enabling more natural conversation 
flow without explicit turn-taking signals.

Closes #42
```

```
fix(clio): handle token refresh edge case

Fixed race condition where multiple concurrent requests could 
attempt to refresh the OAuth token simultaneously, causing some 
requests to fail with 401 errors.

Fixes #87
```

### 🔍 Pull Request Requirements

Every PR must include:

- [ ] Clear description of changes
- [ ] Link to related issue(s)
- [ ] Test coverage for new code
- [ ] Updated documentation (if applicable)
- [ ] Changelog entry (for user-facing changes)
- [ ] Security review (for sensitive changes)
- [ ] Performance impact analysis (for critical paths)

> **📏 PR Size**: Aim for <500 lines of code changes per PR. Larger changes should be split into multiple PRs.

---

## 👀 Code Review Checklist

When reviewing PRs, check for:

### ⚙️ Functionality
- [ ] Code solves the stated problem
- [ ] Edge cases handled
- [ ] Error handling comprehensive
- [ ] Logging appropriate

### 📝 Code Quality
- [ ] Follows coding standards (PEP 8, type hints, docstrings)
- [ ] No code duplication
- [ ] Functions are single-purpose and well-named
- [ ] No commented-out code

### 🔒 Security
- [ ] No hardcoded secrets
- [ ] Input validation implemented
- [ ] No SQL injection vulnerabilities
- [ ] Sensitive data encrypted
- [ ] Audit logging added (if applicable)

### ⚡ Performance
- [ ] No inefficient algorithms
- [ ] Database queries optimized
- [ ] Async/await used correctly
- [ ] No memory leaks

### 🧪 Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] E2E tests pass (if applicable)
- [ ] Test coverage maintained/improved

### 📚 Documentation
- [ ] Docstrings updated
- [ ] API docs updated (if applicable)
- [ ] README updated (if applicable)
- [ ] Changelog updated (if user-facing)

---

## ❌ Common Pitfalls to Avoid

### 🚫 Don't Do This

#### 1. Blocking I/O in Async Functions

**❌ BAD**: Blocks the event loop
```python
async def get_data():
    response = requests.get(url)  # Synchronous call!
    return response.json()
```

**✅ GOOD**: Uses async HTTP client
```python
async def get_data():
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

#### 2. Leaking Sensitive Info in Logs

**❌ BAD**: Logs API key
```python
logger.info(f"Using API key: {api_key}")
```

**✅ GOOD**: Logs safely
```python
logger.info(f"Using API key: {api_key[:8]}...")
```

#### 3. Not Handling Rate Limits

**❌ BAD**: No rate limit handling
```python
response = await clio_api.create_matter(data)
```

**✅ GOOD**: Implements backoff
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential())
async def create_matter_with_retry(data):
    return await clio_api.create_matter(data)
```

#### 4. Using Sync Code in Voice Pipeline

**❌ BAD**: Blocks voice stream
```python
def process_audio(audio_chunk):
    result = whisper_model.transcribe(audio_chunk)  # Blocks!
    return result
```

**✅ GOOD**: Async processing
```python
async def process_audio(audio_chunk):
    result = await asyncio.to_thread(
        whisper_model.transcribe, audio_chunk
    )
    return result
```

---

## 🚀 Project-Specific Commands

### 🛠️ Setup Commands

```bash
# Install dependencies
poetry install

# Setup development environment  
./hermes setup

# Run migrations
alembic upgrade head
```

### 💻 Development Commands

```bash
# Run development server
python -m hermes.main

# Run with auto-reload
uvicorn hermes.main:app --reload

# Run tests
pytest

# Run tests with coverage
pytest --cov=hermes --cov-report=html

# Format code
black hermes/
isort hermes/

# Lint code
flake8 hermes/
mypy hermes/
```

### 🐳 Docker Commands

```bash
# Build Docker image
docker build -t hermes:latest .

# Run with Docker Compose
docker-compose up

# Run in production mode
docker-compose -f docker-compose.prod.yml up -d
```

---

## 👥 Special Instructions for Code Review

### 🚨 Priority Levels for Feedback

#### P0 (Blocker) - Must be fixed before merge
- Security vulnerabilities
- Data corruption risks
- Compliance violations
- Breaking API changes without migration

#### P1 (Critical) - Should be fixed before merge
- Missing error handling
- Performance issues in critical paths
- Missing tests for core functionality
- Incomplete documentation

#### P2 (Important) - Should be fixed soon
- Code quality issues (naming, structure)
- Missing docstrings
- Minor performance improvements
- Style violations

#### P3 (Nice to Have) - Can be fixed later
- Refactoring suggestions
- Additional test coverage
- Documentation improvements

### ⏰ Review Response Time

| Priority | Response Time |
|----------|---------------|
| **P0 Issues** | Fix immediately, within 2 hours |
| **P1 Issues** | Fix within 24 hours |
| **P2 Issues** | Fix within 1 week or create follow-up issue |
| **P3 Issues** | Create follow-up issue for future sprint |

### 🤔 When in Doubt

- **🔒 Prioritize Security**: When unsure, default to the more secure option
- **❓ Ask Questions**: Tag @clduab11 (Chris) for architectural decisions
- **📖 Check Documentation**: Refer to official docs for integrations (Clio, OpenRouter, etc.)
- **🧪 Test Thoroughly**: If it's not tested, it's not done
- **📝 Document Decisions**: Use inline comments for non-obvious choices

---

## 📚 Useful Resources

| Resource | URL |
|----------|-----|
| **FastAPI Docs** | https://fastapi.tiangolo.com/ |
| **Whisper API** | https://platform.openai.com/docs/guides/speech-to-text |
| **Clio API** | https://docs.clio.com/ |
| **OpenRouter** | https://openrouter.ai/docs |
| **Supabase** | https://supabase.com/docs |
| **Mem0** | https://docs.mem0.ai/ |
| **Playwright** | https://playwright.dev/python/ |

---

## 📄 Document Info

- **Last Updated**: 2025-09-30
- **Maintainer**: Chris (clduab11) - Parallax Analytics  
- **Project**: https://github.com/clduab11/hermes-agent

---

> 🚀 **Remember**: Quality code is not just about making it work—it's about making it **secure**, **maintainable**, **performant**, and **compliant** with legal industry standards.