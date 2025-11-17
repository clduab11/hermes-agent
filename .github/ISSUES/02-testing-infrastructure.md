# [PRODUCTION] Comprehensive Testing Infrastructure & 80%+ Coverage

**Status**: 🔴 Critical - Production Blocker
**Priority**: P0 - Immediate
**Estimated Effort**: 48 hours
**Target Completion**: 81% → 100% Production Ready
**Dependencies**: None
**Current Coverage**: ~35% → Target: 80%+

---

## Executive Summary

Implement production-grade testing infrastructure for HERMES to achieve:
- ✅ 80%+ code coverage across all modules
- ✅ Automated testing in CI/CD pipeline
- ✅ Performance and load testing
- ✅ Security testing integration
- ✅ Continuous quality monitoring

**Current State**: 20 test files, fragmented structure, no coverage tracking
**Target State**: Comprehensive test suite with 150+ tests, 80%+ coverage

---

## Phase 1: Test Suite Reorganization (3 hours)

### 1.1 Restructure Test Directory
**Current**:
```
tests/
├── test_*.py (mixed unit/integration)
├── auth/
├── integration/
├── performance/
└── security/
```

**Target Structure**:
```
tests/
├── unit/
│   ├── api/
│   ├── auth/
│   ├── billing/
│   ├── database/
│   ├── integrations/
│   ├── reasoning/
│   ├── services/
│   ├── tts/
│   ├── utils/
│   └── voice/
├── integration/
│   ├── api/
│   ├── auth_flow/
│   ├── billing_flow/
│   ├── clio_integration/
│   ├── database/
│   ├── lawpay_integration/
│   └── voice_pipeline/
├── e2e/
│   ├── complete_call_flow/
│   ├── matter_creation/
│   └── user_onboarding/
├── performance/
│   ├── load_tests/
│   ├── stress_tests/
│   └── benchmarks/
├── security/
│   ├── authentication/
│   ├── authorization/
│   ├── input_validation/
│   └── vulnerability_scans/
├── fixtures/
│   ├── __init__.py
│   ├── api_fixtures.py
│   ├── auth_fixtures.py
│   ├── database_fixtures.py
│   └── mock_data.py
├── conftest.py
├── pytest.ini
└── README.md
```

**Tasks**:
- [ ] Create new directory structure
- [ ] Move existing tests to appropriate locations
- [ ] Create `conftest.py` for each directory
- [ ] Update import paths
- [ ] Remove duplicate tests
- [ ] Document test organization

---

## Phase 2: Pytest Configuration (2 hours)

### 2.1 pytest.ini
**File**: `pytest.ini`

```ini
[pytest]
# Test discovery
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
testpaths = tests

# Output options
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=hermes
    --cov-branch
    --cov-report=html:htmlcov
    --cov-report=term-missing:skip-covered
    --cov-report=xml
    --cov-fail-under=80
    --maxfail=3
    --durations=10
    --color=yes

# Markers for test categorization
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (require external services)
    e2e: End-to-end tests (full workflow)
    slow: Tests that take >1 second
    security: Security-focused tests
    performance: Performance and load tests
    smoke: Smoke tests for critical paths
    regression: Regression tests
    ci: Tests that run in CI pipeline
    local: Tests that run only locally
    requires_api_key: Tests requiring external API keys
    requires_database: Tests requiring database connection

# Coverage configuration
[coverage:run]
source = hermes
omit =
    */tests/*
    */venv/*
    */__pycache__/*
    */site-packages/*
    hermes/__init__.py
    hermes/main.py

[coverage:report]
precision = 2
show_missing = True
skip_covered = False
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
    @abc.abstractmethod
```

### 2.2 .coveragerc
**File**: `.coveragerc`

```ini
[run]
branch = True
source = hermes
omit =
    */tests/*
    */venv/*
    */__pycache__/*
    hermes/__init__.py

[report]
precision = 2
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod

[html]
directory = htmlcov
```

**Tasks**:
- [ ] Create pytest.ini with comprehensive configuration
- [ ] Configure coverage settings
- [ ] Define test markers
- [ ] Set coverage thresholds (80%)
- [ ] Configure output formats

---

## Phase 3: Root conftest.py (3 hours)

**File**: `tests/conftest.py`

```python
"""
Root conftest.py for HERMES test suite
Provides shared fixtures, configuration, and test utilities
"""
import os
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from redis import asyncio as aioredis

# Set testing environment
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5434/hermes_test"
os.environ["REDIS_URL"] = "redis://localhost:6380/0"

from hermes.main import app
from hermes.database.connection import get_db

# ===== Event Loop Configuration =====
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# ===== Database Fixtures =====
@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        echo=False,
        pool_pre_ping=True,
    )
    yield engine
    await engine.dispose()

@pytest.fixture(scope="session")
async def test_session_factory(test_engine):
    """Create session factory"""
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

@pytest.fixture
async def db_session(test_session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Provide database session for tests"""
    async with test_session_factory() as session:
        yield session
        await session.rollback()

# ===== Redis Fixtures =====
@pytest.fixture
async def redis_client():
    """Provide Redis client for tests"""
    client = await aioredis.from_url(
        os.environ["REDIS_URL"],
        encoding="utf-8",
        decode_responses=True,
    )
    yield client
    await client.flushdb()
    await client.close()

# ===== API Client Fixtures =====
@pytest.fixture
def api_client() -> TestClient:
    """Provide FastAPI test client"""
    return TestClient(app)

@pytest.fixture
async def async_api_client():
    """Provide async FastAPI test client"""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

# ===== Authentication Fixtures =====
@pytest.fixture
def mock_user():
    """Provide mock user data"""
    return {
        "id": "test-user-123",
        "email": "test@lawfirm.com",
        "username": "testuser",
        "is_active": True,
        "is_verified": True,
        "firm_name": "Test Law Firm",
        "subscription_tier": "professional",
    }

@pytest.fixture
def auth_headers(mock_user):
    """Provide authentication headers"""
    from hermes.auth.jwt import create_access_token
    token = create_access_token(data={"sub": mock_user["id"]})
    return {"Authorization": f"Bearer {token}"}

# ===== Mock Service Fixtures =====
@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    mock = AsyncMock()
    mock.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="Test response"))]
    )
    return mock

@pytest.fixture
def mock_whisper_client():
    """Mock Whisper STT client"""
    mock = AsyncMock()
    mock.transcribe.return_value = {"text": "Test transcription"}
    return mock

@pytest.fixture
def mock_clio_client():
    """Mock Clio API client"""
    mock = AsyncMock()
    mock.create_matter.return_value = {"id": "matter-123", "status": "open"}
    return mock

@pytest.fixture
def mock_stripe_client():
    """Mock Stripe billing client"""
    mock = AsyncMock()
    mock.checkout.sessions.create.return_value = Mock(url="https://stripe.com/checkout")
    return mock

# ===== Test Data Fixtures =====
@pytest.fixture
def sample_audio_file(tmp_path):
    """Provide sample audio file for testing"""
    import wave
    import numpy as np

    audio_file = tmp_path / "test_audio.wav"
    sample_rate = 16000
    duration = 1
    frequency = 440

    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)

    with wave.open(str(audio_file), 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())

    return audio_file

@pytest.fixture
def sample_legal_matter():
    """Provide sample legal matter data"""
    return {
        "client_name": "John Doe",
        "matter_type": "Personal Injury",
        "description": "Car accident case",
        "jurisdiction": "California",
        "status": "open",
        "billing_method": "hourly",
        "hourly_rate": 350.00,
    }

# ===== Cleanup Fixtures =====
@pytest.fixture(autouse=True)
async def cleanup_after_test(db_session, redis_client):
    """Automatic cleanup after each test"""
    yield
    # Cleanup database
    await db_session.rollback()
    # Cleanup Redis
    await redis_client.flushdb()

# ===== Performance Monitoring =====
@pytest.fixture(autouse=True)
def monitor_test_performance(request):
    """Monitor test execution time"""
    import time
    start = time.time()
    yield
    duration = time.time() - start
    if duration > 1.0:
        print(f"\n⚠️  Slow test: {request.node.nodeid} took {duration:.2f}s")
```

**Tasks**:
- [ ] Create comprehensive root conftest.py
- [ ] Add database fixtures
- [ ] Add Redis fixtures
- [ ] Add authentication fixtures
- [ ] Add mock service fixtures
- [ ] Add test data generators
- [ ] Add cleanup automation

---

## Phase 4: Unit Tests - Core Modules (8 hours)

### 4.1 Authentication Tests
**File**: `tests/unit/auth/test_jwt.py`

```python
"""Unit tests for JWT authentication"""
import pytest
from datetime import datetime, timedelta
from jose import jwt
from hermes.auth.jwt import (
    create_access_token,
    create_refresh_token,
    verify_token,
    decode_token,
)
from hermes.config import get_settings

settings = get_settings()

class TestJWTCreation:
    """Test JWT token creation"""

    def test_create_access_token(self):
        """Should create valid access token"""
        data = {"sub": "user123"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == "user123"
        assert "exp" in payload

    def test_create_token_with_custom_expiry(self):
        """Should create token with custom expiration"""
        data = {"sub": "user123"}
        expires_delta = timedelta(hours=2)
        token = create_access_token(data, expires_delta=expires_delta)

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        exp_timestamp = payload["exp"]
        exp_time = datetime.fromtimestamp(exp_timestamp)
        now = datetime.utcnow()

        # Should expire in ~2 hours
        time_diff = (exp_time - now).total_seconds()
        assert 7000 < time_diff < 7400  # ~2 hours with tolerance

    def test_create_refresh_token(self):
        """Should create valid refresh token"""
        data = {"sub": "user123"}
        token = create_refresh_token(data)

        assert token is not None
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"

class TestJWTVerification:
    """Test JWT token verification"""

    def test_verify_valid_token(self):
        """Should verify valid token"""
        data = {"sub": "user123"}
        token = create_access_token(data)

        is_valid = verify_token(token)
        assert is_valid is True

    def test_verify_expired_token(self):
        """Should reject expired token"""
        data = {"sub": "user123"}
        expires_delta = timedelta(seconds=-1)  # Already expired
        token = create_access_token(data, expires_delta=expires_delta)

        is_valid = verify_token(token)
        assert is_valid is False

    def test_verify_invalid_signature(self):
        """Should reject token with invalid signature"""
        data = {"sub": "user123"}
        token = create_access_token(data)

        # Tamper with token
        parts = token.split('.')
        parts[2] = "invalid_signature"
        invalid_token = '.'.join(parts)

        is_valid = verify_token(invalid_token)
        assert is_valid is False

    def test_decode_token(self):
        """Should decode and return payload"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)

        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"

@pytest.mark.security
class TestJWTSecurity:
    """Test JWT security features"""

    def test_token_contains_no_sensitive_data(self):
        """Should not include sensitive data in token"""
        data = {
            "sub": "user123",
            "password": "should_not_be_included"  # Sensitive
        }
        token = create_access_token(data)
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        assert "password" not in payload

    def test_token_algorithm_cannot_be_none(self):
        """Should reject tokens with 'none' algorithm"""
        # Create token with 'none' algorithm (security vulnerability)
        payload = {"sub": "user123"}
        malicious_token = jwt.encode(payload, None, algorithm="none")

        is_valid = verify_token(malicious_token)
        assert is_valid is False
```

**Coverage Target**: 95%+ for auth module
**Test Count**: 40+ tests

**Additional Unit Test Files to Create**:
- [ ] `tests/unit/auth/test_middleware.py` (15 tests)
- [ ] `tests/unit/auth/test_password_hashing.py` (12 tests)
- [ ] `tests/unit/billing/test_stripe_integration.py` (20 tests)
- [ ] `tests/unit/database/test_models.py` (25 tests)
- [ ] `tests/unit/database/test_connection_pool.py` (10 tests)
- [ ] `tests/unit/reasoning/test_tree_of_thought.py` (18 tests)
- [ ] `tests/unit/reasoning/test_monte_carlo.py` (15 tests)
- [ ] `tests/unit/voice/test_whisper_stt.py` (12 tests)
- [ ] `tests/unit/voice/test_kokoro_tts.py` (12 tests)
- [ ] `tests/unit/voice/test_pipeline.py` (20 tests)
- [ ] `tests/unit/integrations/test_clio_client.py` (25 tests)
- [ ] `tests/unit/integrations/test_lawpay_client.py` (15 tests)
- [ ] `tests/unit/utils/test_rate_limiting.py` (10 tests)
- [ ] `tests/unit/utils/test_validation.py` (15 tests)
- [ ] `tests/unit/api/test_endpoints.py` (30 tests)

---

## Phase 5: Integration Tests (6 hours)

### 5.1 Database Integration Tests
**File**: `tests/integration/database/test_db_operations.py`

```python
"""Integration tests for database operations"""
import pytest
from sqlalchemy import select
from hermes.database.models import User, Matter, Firm
from hermes.database.connection import get_db

@pytest.mark.integration
@pytest.mark.requires_database
class TestUserOperations:
    """Test user database operations"""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """Should create user in database"""
        user = User(
            email="test@lawfirm.com",
            username="testuser",
            hashed_password="hashed_pw",
            firm_name="Test Firm",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.email == "test@lawfirm.com"
        assert user.created_at is not None

    @pytest.mark.asyncio
    async def test_query_user_by_email(self, db_session, mock_user):
        """Should query user by email"""
        # Create user
        user = User(**mock_user)
        db_session.add(user)
        await db_session.commit()

        # Query
        stmt = select(User).where(User.email == mock_user["email"])
        result = await db_session.execute(stmt)
        queried_user = result.scalar_one_or_none()

        assert queried_user is not None
        assert queried_user.email == mock_user["email"]

    @pytest.mark.asyncio
    async def test_update_user(self, db_session, mock_user):
        """Should update user data"""
        user = User(**mock_user)
        db_session.add(user)
        await db_session.commit()

        # Update
        user.firm_name = "Updated Firm Name"
        await db_session.commit()
        await db_session.refresh(user)

        assert user.firm_name == "Updated Firm Name"

    @pytest.mark.asyncio
    async def test_delete_user(self, db_session, mock_user):
        """Should delete user from database"""
        user = User(**mock_user)
        db_session.add(user)
        await db_session.commit()
        user_id = user.id

        # Delete
        await db_session.delete(user)
        await db_session.commit()

        # Verify deletion
        stmt = select(User).where(User.id == user_id)
        result = await db_session.execute(stmt)
        deleted_user = result.scalar_one_or_none()

        assert deleted_user is None
```

**Integration Test Files to Create**:
- [ ] `tests/integration/api/test_auth_flow.py` (15 tests)
- [ ] `tests/integration/api/test_matter_endpoints.py` (20 tests)
- [ ] `tests/integration/clio_integration/test_oauth_flow.py` (12 tests)
- [ ] `tests/integration/clio_integration/test_matter_sync.py` (15 tests)
- [ ] `tests/integration/voice_pipeline/test_full_pipeline.py` (18 tests)
- [ ] `tests/integration/billing_flow/test_subscription_flow.py` (12 tests)
- [ ] `tests/integration/database/test_transactions.py` (10 tests)
- [ ] `tests/integration/database/test_migrations.py` (8 tests)

---

## Phase 6: End-to-End Tests (5 hours)

### 6.1 Complete Call Flow E2E Test
**File**: `tests/e2e/test_complete_call_flow.py`

```python
"""End-to-end test for complete call flow"""
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteCallFlow:
    """Test complete voice call workflow"""

    @pytest.mark.asyncio
    async def test_complete_intake_call(
        self,
        api_client,
        mock_user,
        mock_whisper_client,
        mock_openai_client,
        mock_clio_client,
        sample_audio_file,
    ):
        """Should handle complete intake call from start to finish"""

        # 1. User authentication
        auth_response = api_client.post(
            "/api/v1/auth/login",
            json={
                "email": mock_user["email"],
                "password": "testpassword123",
            },
        )
        assert auth_response.status_code == 200
        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Start voice session
        with patch("hermes.voice.whisper_client", mock_whisper_client), \
             patch("hermes.reasoning.openai_client", mock_openai_client), \
             patch("hermes.integrations.clio_client", mock_clio_client):

            session_response = api_client.post(
                "/api/v1/voice/session/start",
                headers=headers,
            )
            assert session_response.status_code == 200
            session_id = session_response.json()["session_id"]

            # 3. Upload audio file
            with open(sample_audio_file, "rb") as audio:
                audio_response = api_client.post(
                    f"/api/v1/voice/session/{session_id}/audio",
                    files={"audio": audio},
                    headers=headers,
                )
            assert audio_response.status_code == 200
            transcription = audio_response.json()["transcription"]

            # 4. Process through reasoning engine
            reasoning_response = api_client.post(
                f"/api/v1/reasoning/process",
                json={
                    "session_id": session_id,
                    "user_input": transcription,
                },
                headers=headers,
            )
            assert reasoning_response.status_code == 200
            ai_response = reasoning_response.json()["response"]

            # 5. Create matter in Clio
            matter_response = api_client.post(
                "/api/v1/matters/create",
                json={
                    "client_name": "John Doe",
                    "matter_type": "Personal Injury",
                    "description": "Extracted from call",
                },
                headers=headers,
            )
            assert matter_response.status_code == 201
            matter_id = matter_response.json()["matter_id"]

            # 6. Verify matter creation
            assert matter_id is not None
            assert mock_clio_client.create_matter.called

            # 7. End session
            end_response = api_client.post(
                f"/api/v1/voice/session/{session_id}/end",
                headers=headers,
            )
            assert end_response.status_code == 200

            # 8. Verify session summary
            summary = end_response.json()["summary"]
            assert summary["session_id"] == session_id
            assert summary["matter_created"] is True
            assert summary["duration_seconds"] > 0
```

**E2E Test Files to Create**:
- [ ] `tests/e2e/test_matter_creation_flow.py` (8 tests)
- [ ] `tests/e2e/test_user_onboarding_flow.py` (10 tests)
- [ ] `tests/e2e/test_billing_subscription_flow.py` (12 tests)
- [ ] `tests/e2e/test_multi_tenant_isolation.py` (6 tests)

---

## Phase 7: Performance & Load Tests (4 hours)

### 7.1 Load Testing with Locust
**File**: `tests/performance/locustfile.py`

```python
"""Load tests for HERMES API"""
from locust import HttpUser, task, between

class HERMESUser(HttpUser):
    """Simulate HERMES user behavior"""
    wait_time = between(1, 3)

    def on_start(self):
        """Login before tests"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@lawfirm.com",
            "password": "testpass123",
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def get_dashboard(self):
        """Fetch dashboard data"""
        self.client.get("/api/v1/dashboard", headers=self.headers)

    @task(2)
    def list_matters(self):
        """List matters"""
        self.client.get("/api/v1/matters", headers=self.headers)

    @task(1)
    def create_matter(self):
        """Create new matter"""
        self.client.post(
            "/api/v1/matters",
            json={
                "client_name": "Test Client",
                "matter_type": "Contract Review",
            },
            headers=self.headers,
        )
```

**Performance Test Files**:
- [ ] `tests/performance/test_api_response_times.py` (10 tests)
- [ ] `tests/performance/test_database_queries.py` (12 tests)
- [ ] `tests/performance/test_concurrent_calls.py` (8 tests)
- [ ] `tests/performance/test_memory_usage.py` (6 tests)

---

## Phase 8: Security Tests (3 hours)

### 8.1 Security Vulnerability Tests
**File**: `tests/security/test_input_validation.py`

```python
"""Security tests for input validation"""
import pytest

@pytest.mark.security
class TestSQLInjectionPrevention:
    """Test SQL injection prevention"""

    def test_prevent_sql_injection_in_search(self, api_client, auth_headers):
        """Should prevent SQL injection in search"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--",
        ]

        for malicious_input in malicious_inputs:
            response = api_client.get(
                f"/api/v1/search?q={malicious_input}",
                headers=auth_headers,
            )
            # Should not execute malicious SQL
            assert response.status_code in [200, 400]
            # Database should still be intact
            verify_response = api_client.get("/api/v1/health")
            assert verify_response.status_code == 200

@pytest.mark.security
class TestXSSPrevention:
    """Test XSS prevention"""

    def test_prevent_xss_in_matter_description(self, api_client, auth_headers):
        """Should sanitize XSS in matter descriptions"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
        ]

        for payload in xss_payloads:
            response = api_client.post(
                "/api/v1/matters",
                json={
                    "client_name": "Test",
                    "description": payload,
                },
                headers=auth_headers,
            )

            if response.status_code == 201:
                matter_id = response.json()["id"]
                get_response = api_client.get(
                    f"/api/v1/matters/{matter_id}",
                    headers=auth_headers,
                )
                description = get_response.json()["description"]
                # Should be sanitized
                assert "<script>" not in description
                assert "onerror=" not in description

@pytest.mark.security
class TestAuthenticationBypass:
    """Test authentication bypass attempts"""

    def test_cannot_access_protected_endpoint_without_auth(self, api_client):
        """Should require authentication"""
        response = api_client.get("/api/v1/matters")
        assert response.status_code == 401

    def test_cannot_use_expired_token(self, api_client):
        """Should reject expired tokens"""
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2MDk0NTkyMDB9.invalid"
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = api_client.get("/api/v1/matters", headers=headers)
        assert response.status_code == 401
```

**Security Test Files**:
- [ ] `tests/security/test_authentication_security.py` (15 tests)
- [ ] `tests/security/test_authorization_rbac.py` (12 tests)
- [ ] `tests/security/test_rate_limiting.py` (8 tests)
- [ ] `tests/security/test_secrets_management.py` (6 tests)

---

## Phase 9: Fixtures & Test Data (3 hours)

**File**: `tests/fixtures/api_fixtures.py`

```python
"""API-related test fixtures"""
import pytest
from typing import Dict, Any

@pytest.fixture
def valid_user_registration_data() -> Dict[str, Any]:
    """Valid user registration data"""
    return {
        "email": "newuser@lawfirm.com",
        "username": "newuser",
        "password": "SecurePass123!",
        "firm_name": "New Law Firm LLP",
        "phone_number": "+1-555-123-4567",
    }

@pytest.fixture
def invalid_user_registration_data() -> Dict[str, Any]:
    """Invalid user registration data for validation tests"""
    return {
        "email": "invalid-email",  # Invalid email format
        "username": "ab",  # Too short
        "password": "weak",  # Too weak
    }

@pytest.fixture
def sample_matters_list():
    """Sample list of matters for testing"""
    return [
        {
            "id": f"matter-{i}",
            "client_name": f"Client {i}",
            "matter_type": "Personal Injury",
            "status": "open",
            "created_at": "2025-01-01T00:00:00Z",
        }
        for i in range(10)
    ]
```

**Fixture Files**:
- [ ] `tests/fixtures/auth_fixtures.py` (20 fixtures)
- [ ] `tests/fixtures/database_fixtures.py` (15 fixtures)
- [ ] `tests/fixtures/mock_data.py` (25 fixtures)
- [ ] `tests/fixtures/api_responses.py` (18 fixtures)

---

## Phase 10: Test Utilities (2 hours)

**File**: `tests/utils/assertions.py`

```python
"""Custom test assertions"""
from typing import Dict, Any

def assert_valid_uuid(value: str):
    """Assert value is valid UUID"""
    import uuid
    try:
        uuid.UUID(value)
    except ValueError:
        raise AssertionError(f"{value} is not a valid UUID")

def assert_iso_datetime(value: str):
    """Assert value is valid ISO datetime"""
    from datetime import datetime
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise AssertionError(f"{value} is not a valid ISO datetime")

def assert_response_schema(response: Dict[str, Any], schema: Dict[str, type]):
    """Assert response matches schema"""
    for key, expected_type in schema.items():
        assert key in response, f"Missing key: {key}"
        assert isinstance(response[key], expected_type), \
            f"{key} should be {expected_type}, got {type(response[key])}"
```

**Utility Files**:
- [ ] `tests/utils/factories.py` (Model factories)
- [ ] `tests/utils/helpers.py` (Test helpers)
- [ ] `tests/utils/comparisons.py` (Custom comparisons)

---

## Phase 11: Mocking & Patching (2 hours)

**File**: `tests/mocks/external_services.py`

```python
"""Mocks for external services"""
from unittest.mock import AsyncMock, Mock

class MockWhisperClient:
    """Mock Whisper STT client"""

    def __init__(self):
        self.transcribe = AsyncMock(return_value={
            "text": "This is a test transcription",
            "language": "en",
            "duration": 5.2,
        })

class MockClioAPI:
    """Mock Clio API client"""

    def __init__(self):
        self.create_matter = AsyncMock(return_value={
            "id": "matter-12345",
            "status": "open",
            "client": {"id": "client-67890"},
        })
        self.get_matter = AsyncMock()
        self.update_matter = AsyncMock()
        self.delete_matter = AsyncMock()

class MockStripeAPI:
    """Mock Stripe API client"""

    def __init__(self):
        self.checkout = Mock()
        self.checkout.sessions.create = Mock(return_value=Mock(
            url="https://checkout.stripe.com/test-session"
        ))
        self.subscriptions = Mock()
        self.customers = Mock()
```

---

## Phase 12: CI/CD Integration (3 hours)

### 12.1 GitHub Actions Test Workflow
**File**: `.github/workflows/tests.yml`

```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: hermes_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5434:5432

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6380:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt -r requirements-ci.txt

      - name: Run unit tests
        run: pytest tests/unit -v --cov=hermes --cov-report=xml

      - name: Run integration tests
        run: pytest tests/integration -v --cov=hermes --cov-append --cov-report=xml
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5434/hermes_test
          REDIS_URL: redis://localhost:6380/0

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

      - name: Check coverage threshold
        run: |
          coverage report --fail-under=80
```

---

## Phase 13: Code Quality Integration (2 hours)

### 13.1 Pre-commit Hooks
**File**: `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88', '--extend-ignore=E203']

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ['--profile', 'black']

  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest tests/unit --maxfail=1
        language: system
        pass_filenames: false
        always_run: true
```

---

## Phase 14: Documentation & Reporting (2 hours)

**File**: `tests/README.md`

```markdown
# HERMES Test Suite Documentation

## Overview
Comprehensive test suite achieving 80%+ code coverage.

## Structure
- `unit/`: Fast, isolated unit tests
- `integration/`: Integration tests with external services
- `e2e/`: End-to-end workflow tests
- `performance/`: Load and performance tests
- `security/`: Security and vulnerability tests

## Running Tests

### All Tests
\`\`\`bash
pytest
\`\`\`

### By Category
\`\`\`bash
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests
pytest -m e2e           # End-to-end tests
pytest -m security      # Security tests
\`\`\`

### Coverage Report
\`\`\`bash
pytest --cov=hermes --cov-report=html
open htmlcov/index.html
\`\`\`

## Writing Tests

### Unit Test Template
\`\`\`python
import pytest

class TestFeature:
    def test_success_case(self):
        result = feature.do_something()
        assert result == expected

    def test_error_case(self):
        with pytest.raises(ValueError):
            feature.do_invalid()
\`\`\`

## Coverage Goals
- Overall: 80%+
- Critical paths: 95%+
- Authentication: 95%+
- Billing: 90%+
- Voice pipeline: 85%+
```

---

## Acceptance Criteria

### Coverage Targets
- [ ] Overall code coverage: 80%+
- [ ] Unit test coverage: 85%+
- [ ] Integration test coverage: 75%+
- [ ] Critical paths coverage: 95%+
- [ ] Authentication module: 95%+
- [ ] Billing module: 90%+
- [ ] Voice pipeline: 85%+
- [ ] API endpoints: 80%+

### Test Quality
- [ ] All tests pass in CI/CD
- [ ] No flaky tests (<1% failure rate)
- [ ] Fast unit tests (<1s each)
- [ ] Clear test names and documentation
- [ ] Proper use of fixtures and mocks
- [ ] Security tests cover OWASP Top 10

### Infrastructure
- [ ] pytest.ini configured
- [ ] conftest.py with shared fixtures
- [ ] Pre-commit hooks active
- [ ] CI/CD pipeline integrated
- [ ] Coverage reports generated
- [ ] Test documentation complete

---

## Progress Tracking

| Phase | Tests | Coverage | Status | Hours |
|-------|-------|----------|--------|-------|
| 1. Test Reorganization | - | - | ⬜ | 3 |
| 2. Pytest Configuration | - | - | ⬜ | 2 |
| 3. Root conftest.py | 25 fixtures | - | ⬜ | 3 |
| 4. Unit Tests | 300+ | 85% | ⬜ | 8 |
| 5. Integration Tests | 100+ | 75% | ⬜ | 6 |
| 6. E2E Tests | 35+ | 70% | ⬜ | 5 |
| 7. Performance Tests | 30+ | - | ⬜ | 4 |
| 8. Security Tests | 50+ | - | ⬜ | 3 |
| 9. Fixtures & Data | 80 fixtures | - | ⬜ | 3 |
| 10. Test Utilities | - | - | ⬜ | 2 |
| 11. Mocking & Patching | - | - | ⬜ | 2 |
| 12. CI/CD Integration | - | - | ⬜ | 3 |
| 13. Code Quality | - | - | ⬜ | 2 |
| 14. Documentation | - | - | ⬜ | 2 |
| **TOTAL** | **~620 tests** | **80%+** | **0%** | **48h** |

---

## Timeline

- **Week 1**: Phases 1-7 (Core testing infrastructure)
- **Week 2**: Phases 8-14 (Quality, security, automation)

**Target**: 81% → 100% production readiness

---

*Issue Template v1.0 - Created for PR #65 - HERMES Production Testing*
