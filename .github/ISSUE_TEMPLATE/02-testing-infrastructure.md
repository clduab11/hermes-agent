---
name: "[MILESTONE 2] Testing Infrastructure & 80%+ Coverage"
about: Implement comprehensive testing infrastructure with 80%+ code coverage
title: "[MILESTONE 2] Testing Infrastructure & 80%+ Coverage"
labels: testing, quality, high-priority, copilot-ready
assignees: ''
---

## 🎯 Objective

Establish comprehensive testing infrastructure with 80%+ code coverage to ensure production reliability and enable confident deployments. Per CLAUDE.md requirements, this includes unit, integration, E2E, and security tests.

**Current Status:** ~50% - 20 test files, coverage unverified
**Target Status:** 80%+ verified code coverage with organized test suite
**Completion Criteria:** All test types implemented, coverage verified, CI/CD integrated

---

## 📋 Prerequisites

- pytest and pytest plugins installed
- Test database configured
- Mock services configured (Clio, LawPay, OpenRouter)
- Docker environment available (from Milestone 1)
- Understanding of HERMES architecture

---

## ✅ Acceptance Criteria

- [ ] Test directory reorganized into unit/, integration/, e2e/
- [ ] Shared test fixtures and factories created
- [ ] 80%+ code coverage achieved (verified with pytest-cov)
- [ ] Unit tests for all core modules (voice, reasoning, auth)
- [ ] Integration tests for all external services
- [ ] E2E tests for critical user flows
- [ ] Security tests for OWASP Top 10
- [ ] Performance/load tests implemented
- [ ] All tests pass in CI/CD pipeline
- [ ] Test documentation created

---

## 📝 Step-by-Step Implementation Guide

### PHASE 1: Reorganize Test Directory Structure

**Current Structure:**
```
tests/
├── auth/
├── integration/
├── security/
├── performance/
└── *.py (scattered test files)
```

**Target Structure:**
```
tests/
├── unit/                    # Unit tests (isolated, fast)
│   ├── core/
│   ├── auth/
│   ├── services/
│   └── integrations/
├── integration/             # Integration tests (with deps)
│   ├── database/
│   ├── external_apis/
│   └── caching/
├── e2e/                     # End-to-end tests (full flows)
│   ├── voice_pipeline/
│   ├── client_intake/
│   └── payment_flow/
├── security/                # Security-specific tests
├── performance/             # Load and performance tests
├── conftest.py             # Shared fixtures
├── factories.py            # Test data factories
└── helpers.py              # Test utilities
```

**Tasks:**

- [ ] Create directory structure:
  ```bash
  mkdir -p tests/{unit/{core,auth,services,integrations},integration/{database,external_apis,caching},e2e/{voice_pipeline,client_intake,payment_flow}}
  ```

- [ ] Create `__init__.py` in all test directories:
  ```bash
  find tests -type d -exec touch {}/__init__.py \;
  ```

- [ ] Move existing test files to appropriate directories:
  ```bash
  # Map out current tests and move them
  # Example:
  mv tests/test_voice_pipeline.py tests/unit/core/
  mv tests/test_*_integration.py tests/integration/external_apis/
  mv tests/e2e_test_suite.py tests/e2e/
  ```

- [ ] Update import paths in all moved test files

- [ ] Verify tests still run: `pytest tests/ -v`

---

### PHASE 2: Create Shared Test Infrastructure

**File:** `tests/conftest.py`

```python
"""
Shared pytest fixtures and configuration for all tests.
"""
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from redis import asyncio as aioredis

from hermes.main import app
from hermes.database.models import Base
from hermes.config import get_settings


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (with dependencies)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (full user flows)")
    config.addinivalue_line("markers", "slow: Slow-running tests")
    config.addinivalue_line("markers", "security: Security-specific tests")


# ============================================================================
# Event Loop Fixture (for async tests)
# ============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Settings Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_settings():
    """Override settings for testing."""
    settings = get_settings()
    settings.ENV = "test"
    settings.DATABASE_URL = "postgresql+asyncpg://hermes:test@localhost:5432/hermes_test"
    settings.REDIS_URL = "redis://localhost:6379/1"  # Use DB 1 for tests
    settings.DEBUG = True
    return settings


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
async def test_engine(test_settings):
    """Create test database engine."""
    engine = create_async_engine(
        test_settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for a test."""
    async_session_maker = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


# ============================================================================
# Redis Fixtures
# ============================================================================

@pytest.fixture(scope="session")
async def redis_client(test_settings):
    """Create Redis client for tests."""
    client = await aioredis.from_url(
        test_settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    yield client
    await client.flushdb()  # Clear test data
    await client.close()


@pytest.fixture
async def redis(redis_client):
    """Provide Redis client with automatic cleanup."""
    yield redis_client
    await redis_client.flushdb()


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for API testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def authenticated_client(api_client, test_user_token) -> AsyncClient:
    """Create authenticated API client."""
    api_client.headers.update({"Authorization": f"Bearer {test_user_token}"})
    return api_client


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
def test_user_token(test_settings) -> str:
    """Generate a test JWT token."""
    from hermes.auth.jwt_handler import create_access_token

    token_data = {
        "sub": "test-user-123",
        "tenant_id": "test-tenant-123",
        "role": "admin"
    }
    return create_access_token(token_data)


@pytest.fixture
def test_api_key() -> str:
    """Provide test API key."""
    return "test_api_key_12345"


# ============================================================================
# Mock External Services
# ============================================================================

@pytest.fixture
def mock_openrouter(mocker):
    """Mock OpenRouter API calls."""
    mock_response = {
        "choices": [{
            "message": {
                "content": "This is a test AI response.",
                "role": "assistant"
            }
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }

    mock = mocker.patch("httpx.AsyncClient.post")
    mock.return_value.json.return_value = mock_response
    mock.return_value.status_code = 200
    return mock


@pytest.fixture
def mock_clio_api(mocker):
    """Mock Clio API calls."""
    mock = mocker.patch("hermes.integrations.clio.client.ClioClient._make_request")
    mock.return_value = {"data": {"id": 123, "name": "Test Contact"}}
    return mock


@pytest.fixture
def mock_lawpay_api(mocker):
    """Mock LawPay API calls."""
    mock = mocker.patch("hermes.integrations.lawpay.client.LawPayClient._request")
    mock.return_value = {
        "id": "payment_123",
        "status": "succeeded",
        "amount": 5000
    }
    return mock


@pytest.fixture
def mock_whisper_stt(mocker):
    """Mock Whisper STT."""
    mock = mocker.patch("hermes.speech_to_text.WhisperSTT.transcribe")
    mock.return_value = {
        "text": "This is a test transcription.",
        "confidence": 0.95
    }
    return mock


@pytest.fixture
def mock_kokoro_tts(mocker):
    """Mock Kokoro TTS."""
    mock = mocker.patch("hermes.tts.kokoro.KokoroTTS.synthesize")
    mock.return_value = b"fake_audio_data"
    return mock


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_audio_data() -> bytes:
    """Provide sample audio data for testing."""
    # Simple WAV header + silence
    return b"RIFF" + b"\x00" * 100


@pytest.fixture
def sample_client_data() -> dict:
    """Provide sample client data."""
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0100",
        "matter_type": "Personal Injury",
        "description": "Car accident case"
    }


@pytest.fixture
def sample_matter_data() -> dict:
    """Provide sample matter data."""
    return {
        "client_id": "client_123",
        "matter_type": "Personal Injury",
        "jurisdiction": "CA",
        "description": "Plaintiff was injured in a car accident",
        "status": "Open"
    }
```

**Tasks:**
- [ ] Create `tests/conftest.py` with the above content
- [ ] Install required test dependencies: `pip install pytest-asyncio pytest-mock pytest-cov`
- [ ] Create test database: `createdb hermes_test`
- [ ] Test fixtures work: `pytest tests/ -v --collect-only`

---

**File:** `tests/factories.py`

```python
"""
Test data factories for creating realistic test data.
"""
from datetime import datetime, timedelta
from typing import Optional
import random
import string


class ClientFactory:
    """Factory for creating test client data."""

    @staticmethod
    def create(
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        **kwargs
    ) -> dict:
        """Create a test client."""
        if not name:
            first = random.choice(["John", "Jane", "Michael", "Sarah", "David"])
            last = random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones"])
            name = f"{first} {last}"

        if not email:
            email = f"{name.lower().replace(' ', '.')}@example.com"

        if not phone:
            phone = f"+1-555-{random.randint(0, 9999):04d}"

        return {
            "name": name,
            "email": email,
            "phone": phone,
            **kwargs
        }


class MatterFactory:
    """Factory for creating test matter data."""

    MATTER_TYPES = [
        "Personal Injury",
        "Family Law",
        "Criminal Defense",
        "Estate Planning",
        "Business Law"
    ]

    JURISDICTIONS = ["CA", "NY", "TX", "FL", "IL"]

    @staticmethod
    def create(
        client_id: Optional[str] = None,
        matter_type: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        **kwargs
    ) -> dict:
        """Create a test matter."""
        return {
            "client_id": client_id or f"client_{random.randint(1000, 9999)}",
            "matter_type": matter_type or random.choice(MatterFactory.MATTER_TYPES),
            "jurisdiction": jurisdiction or random.choice(MatterFactory.JURISDICTIONS),
            "description": "Test matter description",
            "status": "Open",
            **kwargs
        }


class PaymentFactory:
    """Factory for creating test payment data."""

    @staticmethod
    def create(
        amount: Optional[int] = None,
        payment_type: str = "retainer",
        **kwargs
    ) -> dict:
        """Create a test payment."""
        return {
            "amount": amount or random.randint(1000, 10000),
            "payment_type": payment_type,
            "currency": "usd",
            "description": "Test payment",
            **kwargs
        }


class AudioFactory:
    """Factory for creating test audio data."""

    @staticmethod
    def create_wav_bytes(duration_ms: int = 1000) -> bytes:
        """Create fake WAV audio bytes."""
        # Simplified WAV header
        header = b"RIFF" + (duration_ms).to_bytes(4, 'little') + b"WAVE"
        data = b"\x00" * duration_ms
        return header + data
```

**Tasks:**
- [ ] Create `tests/factories.py`
- [ ] Add more factories as needed for other domain objects
- [ ] Test factories produce valid data

---

### PHASE 3: Run Initial Coverage Baseline

**Tasks:**

- [ ] Install coverage tools:
  ```bash
  pip install pytest-cov coverage[toml]
  ```

- [ ] Run coverage analysis:
  ```bash
  pytest --cov=hermes --cov-report=html --cov-report=term-missing --cov-report=json
  ```

- [ ] Open HTML report:
  ```bash
  open htmlcov/index.html
  ```

- [ ] Document baseline coverage in issue comment:
  ```
  Baseline Coverage: XX%

  Modules with <80% coverage:
  - hermes/voice_pipeline.py: XX%
  - hermes/reasoning/tree_of_thought.py: XX%
  - hermes/integrations/clio/client.py: XX%
  ...
  ```

- [ ] Create coverage improvement tracking spreadsheet

---

### PHASE 4: Write Unit Tests for Voice Pipeline

**File:** `tests/unit/core/test_voice_pipeline.py`

```python
"""
Unit tests for voice pipeline.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from hermes.voice_pipeline import VoicePipeline, VoiceInteraction


@pytest.mark.unit
@pytest.mark.asyncio
class TestVoicePipeline:
    """Test suite for VoicePipeline class."""

    async def test_initialization(self):
        """Test voice pipeline can be initialized."""
        pipeline = VoicePipeline()
        assert pipeline is not None
        assert not pipeline._initialized

    async def test_initialize_success(self, mock_whisper_stt, mock_kokoro_tts):
        """Test successful pipeline initialization."""
        pipeline = VoicePipeline()
        await pipeline.initialize()

        assert pipeline._initialized
        assert pipeline.stt is not None
        assert pipeline.tts is not None

    async def test_process_voice_interaction(
        self,
        sample_audio_data,
        mock_whisper_stt,
        mock_openrouter,
        mock_kokoro_tts
    ):
        """Test processing a complete voice interaction."""
        pipeline = VoicePipeline()
        await pipeline.initialize()

        session_id = "test-session-123"
        result = await pipeline.process_voice_interaction(
            session_id=session_id,
            audio_data=sample_audio_data
        )

        assert isinstance(result, VoiceInteraction)
        assert result.transcription is not None
        assert result.ai_response is not None
        assert result.audio_response is not None
        assert result.latency_ms < 5000  # Should be fast in tests

    async def test_process_empty_audio(self):
        """Test handling of empty audio data."""
        pipeline = VoicePipeline()
        await pipeline.initialize()

        with pytest.raises(ValueError, match="Audio data cannot be empty"):
            await pipeline.process_voice_interaction(
                session_id="test-session",
                audio_data=b""
            )

    async def test_stt_failure_handling(self, sample_audio_data):
        """Test graceful handling of STT failures."""
        pipeline = VoicePipeline()
        await pipeline.initialize()

        with patch.object(pipeline.stt, "transcribe", side_effect=Exception("STT failed")):
            with pytest.raises(Exception, match="STT failed"):
                await pipeline.process_voice_interaction(
                    session_id="test-session",
                    audio_data=sample_audio_data
                )

    async def test_conversation_history_management(
        self,
        sample_audio_data,
        mock_whisper_stt,
        mock_openrouter,
        mock_kokoro_tts
    ):
        """Test conversation history is maintained across interactions."""
        pipeline = VoicePipeline()
        await pipeline.initialize()

        session_id = "test-session-history"

        # First interaction
        result1 = await pipeline.process_voice_interaction(
            session_id=session_id,
            audio_data=sample_audio_data
        )

        # Second interaction
        result2 = await pipeline.process_voice_interaction(
            session_id=session_id,
            audio_data=sample_audio_data
        )

        # History should contain both interactions
        history = pipeline.get_conversation_history(session_id)
        assert len(history) >= 2

    async def test_latency_measurement(
        self,
        sample_audio_data,
        mock_whisper_stt,
        mock_openrouter,
        mock_kokoro_tts
    ):
        """Test that latency is measured accurately."""
        pipeline = VoicePipeline()
        await pipeline.initialize()

        result = await pipeline.process_voice_interaction(
            session_id="latency-test",
            audio_data=sample_audio_data
        )

        assert result.latency_ms > 0
        assert result.latency_ms < 10000  # Should be under 10s for tests
        assert "stt_latency_ms" in result.metrics
        assert "llm_latency_ms" in result.metrics
        assert "tts_latency_ms" in result.metrics


@pytest.mark.unit
def test_voice_interaction_dataclass():
    """Test VoiceInteraction dataclass."""
    interaction = VoiceInteraction(
        session_id="test",
        transcription="Hello",
        ai_response="Hi there",
        audio_response=b"audio",
        latency_ms=500,
        metrics={"test": "value"}
    )

    assert interaction.session_id == "test"
    assert interaction.latency_ms == 500
```

**Tasks:**
- [ ] Create `tests/unit/core/test_voice_pipeline.py`
- [ ] Run tests: `pytest tests/unit/core/test_voice_pipeline.py -v`
- [ ] Achieve 90%+ coverage for `hermes/voice_pipeline.py`
- [ ] Add edge case tests
- [ ] Add error handling tests

---

### PHASE 5: Write Unit Tests for AI Reasoning

**File:** `tests/unit/core/test_tree_of_thought.py`

```python
"""
Unit tests for Tree of Thought reasoning.
"""
import pytest
from unittest.mock import AsyncMock, patch

from hermes.reasoning.tree_of_thought import (
    TreeOfThoughtReasoner,
    ReasoningPath,
    PathEvaluation
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestTreeOfThoughtReasoner:
    """Test suite for Tree of Thought reasoning."""

    async def test_generate_reasoning_paths(self, mock_openrouter):
        """Test generation of multiple reasoning paths."""
        reasoner = TreeOfThoughtReasoner()
        query = "What type of legal case is this?"

        paths = await reasoner.generate_paths(query, num_paths=3)

        assert len(paths) == 3
        assert all(isinstance(p, ReasoningPath) for p in paths)
        assert all(p.reasoning is not None for p in paths)

    async def test_evaluate_paths(self):
        """Test path evaluation and scoring."""
        reasoner = TreeOfThoughtReasoner()

        paths = [
            ReasoningPath(
                reasoning="Path 1: Strong legal reasoning with citations",
                response="Personal Injury case",
                confidence=0.9
            ),
            ReasoningPath(
                reasoning="Path 2: Weak reasoning, no citations",
                response="Maybe personal injury",
                confidence=0.4
            )
        ]

        evaluations = await reasoner.evaluate_paths(paths)

        assert len(evaluations) == 2
        assert all(isinstance(e, PathEvaluation) for e in evaluations)
        assert evaluations[0].score > evaluations[1].score

    async def test_select_best_path(self):
        """Test selection of best reasoning path."""
        reasoner = TreeOfThoughtReasoner()

        evaluations = [
            PathEvaluation(path_index=0, score=0.9, reasoning_quality=0.95),
            PathEvaluation(path_index=1, score=0.5, reasoning_quality=0.6),
            PathEvaluation(path_index=2, score=0.7, reasoning_quality=0.75)
        ]

        best_index = reasoner.select_best_path(evaluations)

        assert best_index == 0  # Highest score

    async def test_full_tot_reasoning_flow(self, mock_openrouter):
        """Test complete ToT reasoning flow."""
        reasoner = TreeOfThoughtReasoner()
        query = "Client was injured in a car accident. What type of case?"

        result = await reasoner.reason(query)

        assert result.response is not None
        assert result.confidence > 0
        assert result.reasoning_paths is not None
        assert len(result.reasoning_paths) > 0
        assert result.selected_path_index >= 0
```

**File:** `tests/unit/core/test_monte_carlo.py`

```python
"""
Unit tests for Monte Carlo simulation.
"""
import pytest
from unittest.mock import AsyncMock

from hermes.reasoning.monte_carlo import MonteCarloSimulator


@pytest.mark.unit
@pytest.mark.asyncio
class TestMonteCarloSimulator:
    """Test suite for Monte Carlo simulation."""

    async def test_run_simulations(self, mock_openrouter):
        """Test running Monte Carlo simulations."""
        simulator = MonteCarloSimulator()
        reasoning_path = "This is a personal injury case based on..."

        result = await simulator.simulate(
            reasoning_path=reasoning_path,
            num_simulations=10
        )

        assert result.confidence > 0
        assert result.variance >= 0
        assert len(result.simulations) == 10

    async def test_consistency_scoring(self):
        """Test consistency scoring of simulations."""
        simulator = MonteCarloSimulator()

        # Simulations with high consistency
        simulations = [
            {"result": "Personal Injury", "confidence": 0.9},
            {"result": "Personal Injury", "confidence": 0.85},
            {"result": "Personal Injury", "confidence": 0.95}
        ]

        consistency = simulator.calculate_consistency(simulations)

        assert consistency > 0.8  # Should be high

    async def test_low_consistency_detection(self):
        """Test detection of low consistency."""
        simulator = MonteCarloSimulator()

        # Simulations with low consistency
        simulations = [
            {"result": "Personal Injury", "confidence": 0.9},
            {"result": "Family Law", "confidence": 0.8},
            {"result": "Criminal Defense", "confidence": 0.7}
        ]

        consistency = simulator.calculate_consistency(simulations)

        assert consistency < 0.5  # Should be low
```

**Tasks:**
- [ ] Create both test files
- [ ] Run tests: `pytest tests/unit/core/ -v`
- [ ] Achieve 85%+ coverage for reasoning modules
- [ ] Add tests for edge cases and error conditions

---

### PHASE 6: Write Unit Tests for Authentication

**File:** `tests/unit/auth/test_jwt_handler.py`

```python
"""
Unit tests for JWT authentication.
"""
import pytest
from datetime import datetime, timedelta
import jwt

from hermes.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_token,
    decode_token
)
from hermes.config import get_settings


@pytest.mark.unit
class TestJWTHandler:
    """Test suite for JWT token handling."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "user_123", "tenant_id": "tenant_456"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        decoded = decode_token(token)
        assert decoded["sub"] == "user_123"
        assert decoded["tenant_id"] == "tenant_456"
        assert "exp" in decoded

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "user_123"}
        token = create_refresh_token(data)

        assert isinstance(token, str)
        decoded = decode_token(token)
        assert decoded["sub"] == "user_123"
        assert decoded["type"] == "refresh"

    def test_verify_valid_token(self):
        """Test verification of valid token."""
        data = {"sub": "user_123"}
        token = create_access_token(data)

        is_valid = verify_token(token)
        assert is_valid is True

    def test_verify_expired_token(self):
        """Test detection of expired token."""
        settings = get_settings()
        data = {"sub": "user_123"}

        # Create token that's already expired
        expires = datetime.utcnow() - timedelta(hours=1)
        token = jwt.encode(
            {**data, "exp": expires},
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        with pytest.raises(jwt.ExpiredSignatureError):
            decode_token(token)

    def test_verify_invalid_signature(self):
        """Test detection of invalid signature."""
        data = {"sub": "user_123"}
        token = create_access_token(data)

        # Tamper with token
        tampered = token[:-10] + "tampered!!"

        with pytest.raises(jwt.InvalidTokenError):
            decode_token(tampered)

    def test_token_expiration_time(self):
        """Test token has correct expiration time."""
        settings = get_settings()
        data = {"sub": "user_123"}
        token = create_access_token(data)

        decoded = decode_token(token)
        exp_time = datetime.fromtimestamp(decoded["exp"])
        now = datetime.utcnow()

        # Should expire in ~15 minutes (default)
        time_diff = exp_time - now
        assert 14 <= time_diff.total_seconds() / 60 <= 16
```

**Tasks:**
- [ ] Create `tests/unit/auth/test_jwt_handler.py`
- [ ] Create `tests/unit/auth/test_rbac.py` for role-based access
- [ ] Run tests: `pytest tests/unit/auth/ -v`
- [ ] Achieve 90%+ coverage for auth modules

---

### PHASE 7: Write Integration Tests for External Services

**File:** `tests/integration/external_apis/test_clio_integration.py`

```python
"""
Integration tests for Clio CRM integration.
"""
import pytest
from unittest.mock import AsyncMock, patch
import httpx

from hermes.integrations.clio.client import ClioClient
from hermes.integrations.clio.auth import ClioTokens


@pytest.mark.integration
@pytest.mark.asyncio
class TestClioIntegration:
    """Test suite for Clio integration."""

    async def test_create_contact(self, mock_clio_api):
        """Test creating a contact in Clio."""
        client = ClioClient()
        tokens = ClioTokens(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=9999999999
        )

        contact_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com"
        }

        result = await client.create_contact(tokens, contact_data)

        assert result is not None
        assert "id" in result
        mock_clio_api.assert_called_once()

    async def test_token_refresh(self):
        """Test automatic token refresh."""
        client = ClioClient()

        # Expired tokens
        tokens = ClioTokens(
            access_token="expired",
            refresh_token="refresh_token",
            expires_at=0  # Already expired
        )

        with patch.object(client, "refresh_tokens") as mock_refresh:
            mock_refresh.return_value = ClioTokens(
                access_token="new_access",
                refresh_token="new_refresh",
                expires_at=9999999999
            )

            new_tokens = await client._ensure_valid_tokens(tokens)

            assert new_tokens.access_token == "new_access"
            mock_refresh.assert_called_once()

    async def test_rate_limit_handling(self):
        """Test handling of Clio rate limits."""
        client = ClioClient()

        # Simulate rate limit response
        with patch.object(client, "_make_request") as mock_request:
            mock_request.side_effect = httpx.HTTPStatusError(
                "Rate limited",
                request=AsyncMock(),
                response=AsyncMock(status_code=429)
            )

            tokens = ClioTokens(
                access_token="test",
                refresh_token="test",
                expires_at=9999999999
            )

            with pytest.raises(httpx.HTTPStatusError):
                await client.create_contact(tokens, {})

    async def test_create_matter(self, mock_clio_api):
        """Test creating a matter in Clio."""
        client = ClioClient()
        tokens = ClioTokens(
            access_token="test",
            refresh_token="test",
            expires_at=9999999999
        )

        matter_data = {
            "client_id": 123,
            "description": "Personal injury case",
            "practice_area": "Personal Injury"
        }

        result = await client.create_matter(tokens, matter_data)

        assert result is not None
        assert "id" in result
```

**Tasks:**
- [ ] Create Clio integration tests
- [ ] Create `tests/integration/external_apis/test_lawpay_integration.py`
- [ ] Create `tests/integration/external_apis/test_zapier_integration.py`
- [ ] Create `tests/integration/external_apis/test_openrouter_integration.py`
- [ ] Run: `pytest tests/integration/external_apis/ -v`

---

### PHASE 8: Write Integration Tests for Database

**File:** `tests/integration/database/test_database_operations.py`

```python
"""
Integration tests for database operations.
"""
import pytest
from sqlalchemy import select

from hermes.database.models import User, Tenant, Matter, Contact
from tests.factories import ClientFactory, MatterFactory


@pytest.mark.integration
@pytest.mark.asyncio
class TestDatabaseOperations:
    """Test suite for database CRUD operations."""

    async def test_create_tenant(self, db_session):
        """Test creating a tenant."""
        tenant = Tenant(
            name="Test Law Firm",
            domain="testfirm.com",
            status="active"
        )
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        assert tenant.id is not None
        assert tenant.name == "Test Law Firm"

    async def test_create_user(self, db_session):
        """Test creating a user."""
        tenant = Tenant(name="Firm", domain="firm.com", status="active")
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            email="user@firm.com",
            hashed_password="hashed",
            tenant_id=tenant.id,
            role="admin"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.tenant_id == tenant.id

    async def test_tenant_isolation(self, db_session):
        """Test that tenant data is properly isolated."""
        # Create two tenants with contacts
        tenant1 = Tenant(name="Firm 1", domain="firm1.com", status="active")
        tenant2 = Tenant(name="Firm 2", domain="firm2.com", status="active")
        db_session.add_all([tenant1, tenant2])
        await db_session.flush()

        contact1 = Contact(
            name="Client 1",
            email="client1@example.com",
            tenant_id=tenant1.id
        )
        contact2 = Contact(
            name="Client 2",
            email="client2@example.com",
            tenant_id=tenant2.id
        )
        db_session.add_all([contact1, contact2])
        await db_session.commit()

        # Query should only return tenant1's contacts
        stmt = select(Contact).where(Contact.tenant_id == tenant1.id)
        result = await db_session.execute(stmt)
        contacts = result.scalars().all()

        assert len(contacts) == 1
        assert contacts[0].name == "Client 1"

    async def test_cascading_delete(self, db_session):
        """Test cascading delete behavior."""
        tenant = Tenant(name="Firm", domain="firm.com", status="active")
        db_session.add(tenant)
        await db_session.flush()

        contact = Contact(
            name="Client",
            email="client@example.com",
            tenant_id=tenant.id
        )
        db_session.add(contact)
        await db_session.commit()
        contact_id = contact.id

        # Delete tenant
        await db_session.delete(tenant)
        await db_session.commit()

        # Contact should be deleted too (if cascade configured)
        stmt = select(Contact).where(Contact.id == contact_id)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None
```

**Tasks:**
- [ ] Create database integration tests
- [ ] Test all CRUD operations
- [ ] Test tenant isolation thoroughly
- [ ] Test transactions and rollbacks
- [ ] Run: `pytest tests/integration/database/ -v`

---

### PHASE 9: Write E2E Tests for Critical Flows

**File:** `tests/e2e/test_client_intake_flow.py`

```python
"""
End-to-end test for complete client intake flow.
"""
import pytest

from tests.factories import AudioFactory, ClientFactory


@pytest.mark.e2e
@pytest.mark.asyncio
class TestClientIntakeFlow:
    """Test complete client intake flow from voice call to matter creation."""

    async def test_complete_intake_flow(
        self,
        authenticated_client,
        db_session,
        mock_whisper_stt,
        mock_openrouter,
        mock_kokoro_tts,
        mock_clio_api
    ):
        """Test complete client intake: voice → transcription → analysis → matter creation."""

        # Step 1: Client initiates voice call
        audio_data = AudioFactory.create_wav_bytes(duration_ms=5000)

        response = await authenticated_client.post(
            "/api/v1/voice/process",
            files={"audio": audio_data}
        )
        assert response.status_code == 200
        voice_result = response.json()

        assert "transcription" in voice_result
        assert "ai_response" in voice_result

        # Step 2: System extracts client information
        mock_whisper_stt.return_value = {
            "text": "My name is John Doe, I was injured in a car accident last week.",
            "confidence": 0.95
        }

        # Step 3: Create contact in Clio
        client_data = ClientFactory.create(
            name="John Doe",
            email="john@example.com"
        )

        response = await authenticated_client.post(
            "/api/v1/clients",
            json=client_data
        )
        assert response.status_code == 201
        client_result = response.json()
        client_id = client_result["id"]

        # Step 4: Create matter
        matter_data = {
            "client_id": client_id,
            "matter_type": "Personal Injury",
            "jurisdiction": "CA",
            "description": "Car accident case"
        }

        response = await authenticated_client.post(
            "/api/v1/matters",
            json=matter_data
        )
        assert response.status_code == 201
        matter_result = response.json()

        assert matter_result["client_id"] == client_id
        assert matter_result["matter_type"] == "Personal Injury"

        # Step 5: Verify matter was created in Clio
        mock_clio_api.assert_called()

        # Step 6: Verify audit log entry
        # (Check that the intake was logged)

        # Complete flow successful!
```

**Tasks:**
- [ ] Create E2E test for client intake flow
- [ ] Create `tests/e2e/test_payment_flow.py`
- [ ] Create `tests/e2e/test_voice_pipeline_e2e.py`
- [ ] Use realistic test scenarios
- [ ] Run: `pytest tests/e2e/ -v --tb=short`

---

### PHASE 10: Write Security Tests

**File:** `tests/security/test_owasp_top_10.py`

```python
"""
Security tests for OWASP Top 10 vulnerabilities.
"""
import pytest


@pytest.mark.security
@pytest.mark.asyncio
class TestSQLInjection:
    """Test SQL injection prevention."""

    async def test_sql_injection_in_search(self, authenticated_client):
        """Test that SQL injection is prevented in search queries."""
        # Attempt SQL injection
        malicious_input = "'; DROP TABLE users; --"

        response = await authenticated_client.get(
            f"/api/v1/search?q={malicious_input}"
        )

        # Should not cause error, should sanitize input
        assert response.status_code in [200, 400]
        # Database should still exist
        # (verify with a subsequent valid query)


@pytest.mark.security
@pytest.mark.asyncio
class TestAuthenticationSecurity:
    """Test authentication security."""

    async def test_unauthorized_access_blocked(self, api_client):
        """Test that unauthorized requests are blocked."""
        response = await api_client.get("/api/v1/matters")

        assert response.status_code == 401

    async def test_token_tampering_detected(self, api_client):
        """Test that tampered tokens are rejected."""
        tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.tampered.signature"

        response = await api_client.get(
            "/api/v1/matters",
            headers={"Authorization": f"Bearer {tampered_token}"}
        )

        assert response.status_code == 401

    async def test_rate_limiting_enforced(self, api_client):
        """Test that rate limiting is enforced."""
        # Make many requests rapidly
        responses = []
        for i in range(150):  # Exceed rate limit
            response = await api_client.get("/api/v1/health")
            responses.append(response)

        # Some should be rate limited
        rate_limited = [r for r in responses if r.status_code == 429]
        assert len(rate_limited) > 0


@pytest.mark.security
class TestDataEncryption:
    """Test sensitive data encryption."""

    async def test_passwords_are_hashed(self, db_session):
        """Test that passwords are never stored in plain text."""
        from hermes.database.models import User
        from sqlalchemy import select

        user = User(
            email="test@example.com",
            hashed_password="plaintext_password",  # This should never happen
            role="user"
        )
        db_session.add(user)
        await db_session.commit()

        # Retrieve and verify it's hashed
        stmt = select(User).where(User.email == "test@example.com")
        result = await db_session.execute(stmt)
        retrieved_user = result.scalar_one()

        # Should be hashed (bcrypt, argon2, etc.)
        assert retrieved_user.hashed_password != "plaintext_password"
        assert len(retrieved_user.hashed_password) > 50  # Hashes are long
```

**Tasks:**
- [ ] Create security tests for OWASP Top 10
- [ ] Test XSS prevention
- [ ] Test CSRF protection
- [ ] Test authentication/authorization
- [ ] Run: `pytest tests/security/ -v`

---

### PHASE 11: Write Performance Tests

**File:** `tests/performance/test_load.py`

```python
"""
Load and performance tests.
"""
import pytest
import asyncio
from time import time


@pytest.mark.slow
@pytest.mark.asyncio
async def test_concurrent_voice_processing(authenticated_client, sample_audio_data):
    """Test handling of concurrent voice processing requests."""

    async def process_voice():
        start = time()
        response = await authenticated_client.post(
            "/api/v1/voice/process",
            files={"audio": sample_audio_data}
        )
        latency = (time() - start) * 1000
        return response.status_code, latency

    # Process 50 concurrent requests
    tasks = [process_voice() for _ in range(50)]
    results = await asyncio.gather(*tasks)

    # All should succeed
    assert all(status == 200 for status, _ in results)

    # Average latency should be acceptable
    avg_latency = sum(lat for _, lat in results) / len(results)
    assert avg_latency < 2000  # < 2 seconds average


@pytest.mark.slow
@pytest.mark.asyncio
async def test_database_query_performance(db_session):
    """Test database query performance under load."""
    from hermes.database.models import Matter
    from sqlalchemy import select

    # Create many records
    matters = [
        Matter(
            description=f"Test matter {i}",
            matter_type="Test",
            status="Open"
        )
        for i in range(1000)
    ]
    db_session.add_all(matters)
    await db_session.commit()

    # Query should be fast
    start = time()
    stmt = select(Matter).limit(100)
    result = await db_session.execute(stmt)
    matters = result.scalars().all()
    query_time = (time() - start) * 1000

    assert len(matters) == 100
    assert query_time < 100  # < 100ms
```

**Tasks:**
- [ ] Create performance tests
- [ ] Test API endpoint performance
- [ ] Test database query performance
- [ ] Test voice pipeline latency
- [ ] Document performance benchmarks

---

### PHASE 12: Achieve 80%+ Coverage

**Iterative Coverage Improvement:**

- [ ] Run coverage report:
  ```bash
  pytest --cov=hermes --cov-report=html --cov-report=term-missing
  ```

- [ ] Identify modules below 80%:
  ```bash
  coverage report --skip-covered --show-missing
  ```

- [ ] Prioritize critical modules:
  1. Voice pipeline
  2. Authentication
  3. Integrations (Clio, LawPay)
  4. Database operations
  5. API endpoints

- [ ] Write tests for uncovered code paths

- [ ] Focus on edge cases and error handling

- [ ] Repeat until 80%+ achieved

---

### PHASE 13: Configure CI/CD for Testing

**File:** `.github/workflows/testing.yml`

```yaml
name: Testing & Coverage

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: hermes_test
          POSTGRES_USER: hermes
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-xdist

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=hermes --cov-report=xml

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql+asyncpg://hermes:test_password@localhost:5432/hermes_test
          REDIS_URL: redis://localhost:6379/1
        run: pytest tests/integration/ -v --cov=hermes --cov-append --cov-report=xml

      - name: Run E2E tests
        run: pytest tests/e2e/ -v --cov=hermes --cov-append --cov-report=xml

      - name: Run security tests
        run: pytest tests/security/ -v

      - name: Check coverage threshold
        run: |
          coverage report --fail-under=80

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella
```

**Tasks:**
- [ ] Create `.github/workflows/testing.yml`
- [ ] Configure coverage reporting (Codecov/Coveralls)
- [ ] Make 80% coverage required for PR merges
- [ ] Add coverage badge to README

---

### PHASE 14: Documentation

**File:** `docs/testing-guide.md`

Create comprehensive testing documentation covering:
- How to run tests locally
- How to write new tests
- Test data factories usage
- Mocking strategies
- Coverage requirements
- CI/CD integration

**Tasks:**
- [ ] Create `docs/testing-guide.md`
- [ ] Update CLAUDE.md with testing examples
- [ ] Add testing section to README
- [ ] Document test environment setup

---

## 📊 Validation Checklist

- [ ] Test directory reorganized into unit/, integration/, e2e/
- [ ] Shared fixtures in conftest.py working
- [ ] Test factories created and documented
- [ ] 80%+ code coverage achieved (verified)
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] All E2E tests passing
- [ ] Security tests implemented
- [ ] Performance tests implemented
- [ ] CI/CD runs all tests automatically
- [ ] Coverage reporting integrated
- [ ] Test documentation complete

---

## 🎯 Success Metrics

- Overall code coverage: ≥ 80%
- Voice pipeline coverage: ≥ 90%
- Authentication coverage: ≥ 90%
- Integration coverage: ≥ 75%
- All tests pass in CI/CD
- Test execution time: < 5 minutes
- No flaky tests

---

## 💡 AI Coding Assistant Instructions

**Execution Strategy:**
1. Start with PHASE 1 (reorganization)
2. Create test infrastructure (PHASE 2-3)
3. Write tests module by module (PHASE 4-11)
4. Iterate to achieve 80%+ coverage (PHASE 12)
5. Configure CI/CD (PHASE 13)
6. Complete documentation (PHASE 14)

**Key Points:**
- Run tests frequently to catch regressions
- Use factories for test data (don't hardcode)
- Mock external services (never call real APIs in tests)
- Test both success and failure paths
- Focus on critical code paths first
- Document any skipped tests with reasons

---

**Issue Priority:** 🔴 **HIGH**
**Estimated Complexity:** High
**Blocking:** Production Confidence
**Dependencies:** Milestone 1 (Docker) recommended but not required
**Milestone:** Production Readiness - Phase 2
