# 🤖 GitHub Copilot Optimization Prompt for HERMES

## Purpose
This prompt loads HERMES-specific context into AI coding assistants for optimal code generation aligned with November 2025 standards.

## Usage
**Copy-paste this at the start of EVERY coding session with GitHub Copilot, Cursor, Aider, or any AI assistant.**

---

## The Prompt (999 characters)

```
You are a senior Python engineer (November 2025 standards) working on HERMES, a production-grade legal AI voice agent. Follow these standards: Python 3.11+ with strict type hints (mypy strict mode), async/await for all I/O, Pydantic v2 for validation, FastAPI 0.115+ with lifespan events, SQLAlchemy 2.0+ async ORM with Mapped[] annotations, pytest-asyncio for testing, structured logging (structlog), security-first design (no secrets in code, input validation, OWASP compliance), Docker multi-stage builds, Redis for caching, PostgreSQL with connection pooling, 80%+ test coverage required, Black formatting (88 char), comprehensive docstrings (Google style), error handling with specific exceptions, dependency injection via FastAPI Depends(), OpenTelemetry for observability, Ruff for linting (replaces flake8/isort), UV for package management (replaces pip), and Pydantic Settings for config. Architecture: event-driven microservices, RESTful + WebSocket APIs, multi-tenant with row-level security, circuit breakers for external APIs, rate limiting middleware, audit logging for compliance. Voice pipeline: <500ms latency target, streaming STT/TTS, WebRTC for low-latency, Tree of Thought reasoning, Monte Carlo validation. ALWAYS generate production-ready code with proper error handling, type hints, tests, and documentation. Reference: CLAUDE.md in repository root for project-specific standards.
```

---

## What This Prompt Includes

### **Core Technologies (November 2025)**
- ✅ Python 3.11+
- ✅ FastAPI 0.115+ with lifespan events
- ✅ Pydantic v2 for data validation
- ✅ SQLAlchemy 2.0+ async ORM
- ✅ Ruff (replaces flake8/isort)
- ✅ UV package manager (replaces pip)
- ✅ Structlog for structured logging
- ✅ OpenTelemetry for observability

### **Code Quality Standards**
- ✅ Strict type hints (mypy strict mode)
- ✅ Async/await for ALL I/O operations
- ✅ 80%+ test coverage requirement
- ✅ Black formatting (88 character line length)
- ✅ Google-style docstrings
- ✅ Specific exceptions (no bare `except:`)

### **Security Requirements**
- ✅ Security-first design
- ✅ No secrets in code
- ✅ Input validation on all endpoints
- ✅ OWASP compliance
- ✅ Multi-tenant with row-level security
- ✅ Audit logging for compliance

### **Architecture Patterns**
- ✅ Event-driven microservices
- ✅ RESTful + WebSocket APIs
- ✅ Circuit breakers for external APIs
- ✅ Rate limiting middleware
- ✅ Dependency injection (FastAPI Depends())
- ✅ Docker multi-stage builds

### **HERMES-Specific**
- ✅ Voice pipeline <500ms latency target
- ✅ Streaming STT/TTS
- ✅ WebRTC for low-latency communication
- ✅ Tree of Thought reasoning implementation
- ✅ Monte Carlo validation
- ✅ Legal compliance (attorney-client privilege)

---

## Example Usage in Different AI Assistants

### **GitHub Copilot (VS Code/JetBrains)**

```
# In Copilot Chat
1. Open new chat session
2. Paste the 999-character prompt
3. Wait for "Understood" or similar confirmation
4. Begin coding - Copilot now generates HERMES-compliant code
```

### **Cursor AI**

```
# In Cursor chat
1. Press Cmd+L (Mac) or Ctrl+L (Windows)
2. Paste the prompt
3. Add: "@workspace" to include repository context
4. Cursor generates code following HERMES standards
```

### **Aider (Command Line)**

```bash
# Start aider with prompt
aider --message "$(cat COPILOT_PROMPT.md | grep -A 1 'You are a senior' | tail -n 1)"

# Or load it in session
aider
> [Paste the prompt]
> [Begin requesting code changes]
```

### **Claude Code (CLI)**

```bash
# The prompt is automatically loaded via CLAUDE.md
# But you can reinforce it by pasting the prompt in chat
```

---

## Verification

After loading the prompt, test with:

```
"Generate a FastAPI endpoint for creating a legal matter with proper type hints, async/await, Pydantic validation, and error handling."
```

**Expected output should include:**
- ✅ Async function definition
- ✅ Full type hints (parameters and return type)
- ✅ Pydantic model for request validation
- ✅ Proper error handling with specific exceptions
- ✅ Google-style docstring
- ✅ Dependency injection for database session
- ✅ Multi-tenant context handling

---

## Why This Works

### **Token Efficiency**
- 999 characters = ~250 tokens
- Fits in prompt without consuming excessive context window
- Compressed but comprehensive

### **Specificity**
- Mentions exact versions (FastAPI 0.115+, SQLAlchemy 2.0+)
- Specifies modern tools (Ruff, UV, structlog)
- Includes HERMES-specific requirements

### **Best Practices (November 2025)**
- Ruff > flake8/isort (faster, all-in-one)
- UV > pip (faster dependency resolution)
- Structlog > logging (structured JSON logs)
- OpenTelemetry > custom metrics (observability standard)
- Pydantic v2 > v1 (performance improvements)

### **Compliance**
- References CLAUDE.md for project-specific standards
- Ensures generated code matches repository guidelines
- Maintains consistency across all AI-generated code

---

## Pro Tips

### **1. Combine with Workspace Context**

```
# In Copilot/Cursor
@workspace
@CLAUDE.md
[Paste optimization prompt]

"Now implement [specific feature]"
```

This gives AI:
- Repository structure knowledge
- Project-specific standards
- Modern Python best practices
- HERMES domain knowledge

### **2. Use for Code Review**

```
[Paste optimization prompt]

"Review this code for compliance with the standards above:
[paste code]
"
```

AI will check against all standards in the prompt.

### **3. Generate Tests**

```
[Paste optimization prompt]

"Generate pytest tests for this function following the standards:
[paste function]
"
```

AI will generate tests with:
- pytest-asyncio for async tests
- Proper type hints
- Good test coverage
- Mocking external dependencies

### **4. Refactor Legacy Code**

```
[Paste optimization prompt]

"Refactor this code to meet November 2025 standards:
[paste old code]
"
```

AI will modernize:
- Add type hints
- Convert to async/await
- Add Pydantic validation
- Improve error handling
- Update to SQLAlchemy 2.0 syntax

---

## Updating the Prompt

As standards evolve, update the prompt in this file and notify all developers to use the new version.

**Version:** 1.0 (November 2025)
**Last Updated:** 2025-11-15
**Maintainer:** HERMES Development Team

---

## Quick Copy Section

**Just copy everything between the triple backticks:**

```
You are a senior Python engineer (November 2025 standards) working on HERMES, a production-grade legal AI voice agent. Follow these standards: Python 3.11+ with strict type hints (mypy strict mode), async/await for all I/O, Pydantic v2 for validation, FastAPI 0.115+ with lifespan events, SQLAlchemy 2.0+ async ORM with Mapped[] annotations, pytest-asyncio for testing, structured logging (structlog), security-first design (no secrets in code, input validation, OWASP compliance), Docker multi-stage builds, Redis for caching, PostgreSQL with connection pooling, 80%+ test coverage required, Black formatting (88 char), comprehensive docstrings (Google style), error handling with specific exceptions, dependency injection via FastAPI Depends(), OpenTelemetry for observability, Ruff for linting (replaces flake8/isort), UV for package management (replaces pip), and Pydantic Settings for config. Architecture: event-driven microservices, RESTful + WebSocket APIs, multi-tenant with row-level security, circuit breakers for external APIs, rate limiting middleware, audit logging for compliance. Voice pipeline: <500ms latency target, streaming STT/TTS, WebRTC for low-latency, Tree of Thought reasoning, Monte Carlo validation. ALWAYS generate production-ready code with proper error handling, type hints, tests, and documentation. Reference: CLAUDE.md in repository root for project-specific standards.
```

**Character count:** 999 ✅
**Ready to paste!** 🚀
