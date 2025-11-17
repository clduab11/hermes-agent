"""
Root conftest.py for HERMES Test Suite
Provides shared fixtures, configuration, and test utilities

This file provides comprehensive test fixtures for:
- Database session management (AsyncSession, engine, cleanup)
- Redis client management
- FastAPI test clients (sync and async)
- Authentication (mock users, JWT tokens, auth headers)
- Mock external services (OpenAI, Whisper, Clio, Stripe, LawPay, Zapier)
- Test data generators (audio files, legal matters, users)
- Performance monitoring and cleanup automation

Target: 80%+ code coverage with fast, reliable tests
"""

import asyncio
import os
import wave
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, Generator, Any
from unittest.mock import AsyncMock, Mock

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set testing environment BEFORE imports that depend on it
os.environ["TESTING"] = "1"
os.environ["DEMO_MODE"] = "true"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5434/hermes_test"
os.environ["REDIS_URL"] = "redis://localhost:6380/0"
os.environ["JWT_PRIVATE_KEY"] = "test_private_key_for_testing_only"
os.environ["JWT_PUBLIC_KEY"] = "test_public_key_for_testing_only"
os.environ["JWT_ALGORITHM"] = "HS256"  # Use symmetric for testing
os.environ["OPENAI_API_KEY"] = "sk-test-key-for-testing"
os.environ["SUPABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5434/hermes_test"

from hermes.main import app
from hermes.config import settings
from hermes.auth.jwt_handler import JWTHandler
from hermes.auth.models import Role

# ===== Event Loop Configuration =====


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create event loop for async tests (session-scoped).

    Provides a single event loop for all async tests in the session
    to prevent loop closure issues with pytest-asyncio.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# ===== Database Fixtures =====


@pytest.fixture(scope="session")
async def test_engine():
    """
    Create test database engine (session-scoped).

    Creates async SQLAlchemy engine connected to test database.
    The engine is shared across all tests for performance.
    """
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def test_session_factory(test_engine):
    """
    Create session factory (session-scoped).

    Returns async_sessionmaker for creating database sessions.
    """
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
async def db_session(test_session_factory) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide database session for tests (function-scoped).

    Creates a new database session for each test, automatically
    rolls back changes after the test completes to ensure isolation.

    Usage:
        async def test_create_user(db_session):
            # Use db_session for database operations
            pass
    """
    async with test_session_factory() as session:
        yield session
        await session.rollback()


# ===== Redis Fixtures =====


@pytest.fixture
async def redis_client():
    """
    Provide Redis client for tests (function-scoped).

    Creates Redis client connected to test Redis instance,
    automatically flushes database after each test.

    Usage:
        async def test_cache(redis_client):
            await redis_client.set("key", "value")
            assert await redis_client.get("key") == "value"
    """
    try:
        from redis import asyncio as aioredis

        client = await aioredis.from_url(
            os.environ["REDIS_URL"],
            encoding="utf-8",
            decode_responses=True,
        )
        yield client
        await client.flushdb()
        await client.close()
    except Exception as e:
        # If Redis is not available, return a mock client
        mock_client = AsyncMock()
        mock_client.get.return_value = None
        mock_client.set.return_value = True
        mock_client.delete.return_value = 1
        yield mock_client


# ===== API Client Fixtures =====


@pytest.fixture
def api_client() -> TestClient:
    """
    Provide synchronous FastAPI test client (function-scoped).

    Usage:
        def test_health_endpoint(api_client):
            response = api_client.get("/health")
            assert response.status_code == 200
    """
    return TestClient(app)


@pytest.fixture
async def async_api_client():
    """
    Provide async FastAPI test client (function-scoped).

    Usage:
        async def test_async_endpoint(async_api_client):
            response = await async_api_client.get("/api/v1/matters")
            assert response.status_code == 200
    """
    from httpx import AsyncClient

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ===== Authentication Fixtures =====


@pytest.fixture
def mock_user() -> Dict[str, Any]:
    """
    Provide mock user data (function-scoped).

    Returns a dictionary with standard test user information
    for use in authentication and authorization tests.
    """
    return {
        "id": "test-user-123",
        "email": "test@lawfirm.com",
        "username": "testuser",
        "is_active": True,
        "is_verified": True,
        "firm_name": "Test Law Firm",
        "subscription_tier": "professional",
        "tenant_id": "test-tenant-123",
        "roles": [Role.ADMIN],
    }


@pytest.fixture
def mock_admin_user() -> Dict[str, Any]:
    """Provide mock admin user data."""
    return {
        "id": "admin-user-456",
        "email": "admin@lawfirm.com",
        "username": "adminuser",
        "is_active": True,
        "is_verified": True,
        "firm_name": "Admin Law Firm",
        "subscription_tier": "enterprise",
        "tenant_id": "admin-tenant-456",
        "roles": [Role.ADMIN, Role.SUPER_ADMIN],
    }


@pytest.fixture
def jwt_handler() -> JWTHandler:
    """
    Provide JWT handler for token generation (function-scoped).

    Returns configured JWTHandler for creating test tokens.
    """
    return JWTHandler()


@pytest.fixture
def auth_headers(mock_user, jwt_handler) -> Dict[str, str]:
    """
    Provide authentication headers with valid JWT token (function-scoped).

    Usage:
        def test_protected_endpoint(api_client, auth_headers):
            response = api_client.get("/api/v1/matters", headers=auth_headers)
            assert response.status_code == 200
    """
    token_pair = jwt_handler.create_token_pair(
        subject=mock_user["id"],
        tenant_id=mock_user["tenant_id"],
        roles=mock_user["roles"],
    )
    return {"Authorization": f"Bearer {token_pair.access_token}"}


@pytest.fixture
def admin_auth_headers(mock_admin_user, jwt_handler) -> Dict[str, str]:
    """Provide admin authentication headers with valid JWT token."""
    token_pair = jwt_handler.create_token_pair(
        subject=mock_admin_user["id"],
        tenant_id=mock_admin_user["tenant_id"],
        roles=mock_admin_user["roles"],
    )
    return {"Authorization": f"Bearer {token_pair.access_token}"}


# ===== Mock Service Fixtures =====


@pytest.fixture
def mock_openai_client():
    """
    Mock OpenAI client for LLM tests (function-scoped).

    Returns AsyncMock that simulates OpenAI API responses.

    Usage:
        async def test_reasoning(mock_openai_client):
            # mock_openai_client.chat.completions.create is pre-configured
            pass
    """
    mock = AsyncMock()
    mock.chat.completions.create.return_value = Mock(
        choices=[
            Mock(
                message=Mock(
                    content="Test AI response for legal matter analysis",
                    role="assistant",
                )
            )
        ],
        usage=Mock(prompt_tokens=50, completion_tokens=100, total_tokens=150),
    )
    return mock


@pytest.fixture
def mock_whisper_client():
    """
    Mock Whisper STT client (function-scoped).

    Returns AsyncMock that simulates Whisper speech-to-text responses.
    """
    mock = AsyncMock()
    mock.transcribe.return_value = {
        "text": "This is a test transcription of client speech",
        "language": "en",
        "duration": 5.2,
        "segments": [],
    }
    return mock


@pytest.fixture
def mock_kokoro_client():
    """
    Mock Kokoro TTS client (function-scoped).

    Returns AsyncMock that simulates Kokoro text-to-speech responses.
    """
    mock = AsyncMock()
    mock.synthesize.return_value = b"mock_audio_bytes_pcm_16bit"
    return mock


@pytest.fixture
def mock_clio_client():
    """
    Mock Clio CRM API client (function-scoped).

    Returns AsyncMock that simulates Clio API responses for matter management.
    """
    mock = AsyncMock()
    mock.create_matter.return_value = {
        "id": "matter-123",
        "status": "open",
        "client_id": "client-456",
        "matter_type": "Personal Injury",
        "description": "Car accident case",
    }
    mock.get_matter.return_value = {
        "id": "matter-123",
        "status": "open",
    }
    mock.update_matter.return_value = {
        "id": "matter-123",
        "status": "updated",
    }
    return mock


@pytest.fixture
def mock_stripe_client():
    """
    Mock Stripe billing client (function-scoped).

    Returns AsyncMock that simulates Stripe API responses for billing.
    """
    mock = AsyncMock()
    mock.checkout.sessions.create.return_value = Mock(
        id="cs_test_123",
        url="https://checkout.stripe.com/test",
        payment_status="unpaid",
    )
    mock.subscriptions.create.return_value = Mock(
        id="sub_test_456",
        status="active",
        current_period_end=1234567890,
    )
    return mock


@pytest.fixture
def mock_lawpay_client():
    """
    Mock LawPay payment client (function-scoped).

    Returns AsyncMock that simulates LawPay API responses.
    """
    mock = AsyncMock()
    mock.create_payment.return_value = {
        "payment_id": "lp_123",
        "status": "pending",
        "amount": 500.00,
        "currency": "USD",
    }
    return mock


@pytest.fixture
def mock_zapier_client():
    """
    Mock Zapier webhook client (function-scoped).

    Returns AsyncMock that simulates Zapier webhook responses.
    """
    mock = AsyncMock()
    mock.send_webhook.return_value = {
        "status": "success",
        "hook_id": "zap_789",
    }
    return mock


# ===== Test Data Fixtures =====


@pytest.fixture
def sample_audio_file(tmp_path):
    """
    Generate sample WAV audio file for testing (function-scoped).

    Creates a 1-second 440Hz sine wave at 16kHz sample rate.

    Returns:
        Path to generated WAV file

    Usage:
        def test_audio_processing(sample_audio_file):
            with open(sample_audio_file, 'rb') as f:
                audio_data = f.read()
    """
    audio_file = tmp_path / "test_audio.wav"
    sample_rate = 16000
    duration = 1
    frequency = 440  # A4 note

    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)

    with wave.open(str(audio_file), "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())

    return audio_file


@pytest.fixture
def sample_legal_matter() -> Dict[str, Any]:
    """
    Provide sample legal matter data (function-scoped).

    Returns dictionary with realistic legal matter information
    for testing matter creation and management.
    """
    return {
        "client_name": "John Doe",
        "matter_type": "Personal Injury",
        "description": "Car accident case - client rear-ended at intersection",
        "jurisdiction": "California",
        "status": "open",
        "billing_method": "contingency",
        "contingency_percentage": 33.33,
        "hourly_rate": 350.00,
        "incident_date": "2024-01-15",
        "statute_of_limitations": "2026-01-15",
    }


@pytest.fixture
def sample_client_intake() -> Dict[str, Any]:
    """
    Provide sample client intake data (function-scoped).

    Returns dictionary with client information from intake call.
    """
    return {
        "name": "Jane Smith",
        "email": "jane.smith@email.com",
        "phone": "+1-555-123-4567",
        "matter_summary": "Seeking representation for employment discrimination case",
        "preferred_contact_method": "email",
        "urgency": "medium",
        "referral_source": "Google search",
    }


@pytest.fixture
def sample_conversation_transcript() -> str:
    """
    Provide sample conversation transcript (function-scoped).

    Returns realistic conversation between HERMES and potential client.
    """
    return """
HERMES: Good morning, this is HERMES, the AI receptionist for Johnson & Associates Law Firm. How may I assist you today?

CLIENT: Hi, I was in a car accident last week and I need to speak with a lawyer about my case.

HERMES: I'm sorry to hear about your accident. I'd be happy to help gather some preliminary information. Can you tell me your name?

CLIENT: Yes, it's Michael Rodriguez.

HERMES: Thank you, Michael. Can you briefly describe what happened in the accident?

CLIENT: I was driving through an intersection on a green light when another car ran a red light and hit my driver's side door. I had to go to the hospital.

HERMES: I understand. This sounds like it could be a personal injury case. Let me connect you with one of our attorneys who specializes in motor vehicle accidents.
"""


# ===== Cleanup Fixtures =====


@pytest.fixture(autouse=True)
async def cleanup_after_test(request):
    """
    Automatic cleanup after each test (function-scoped, auto-use).

    Runs after every test to ensure clean state for next test.
    Handles database rollback and Redis flush.
    """
    yield
    # Cleanup is handled by individual fixtures (db_session, redis_client)
    # This fixture exists for future cleanup needs


# ===== Performance Monitoring =====


@pytest.fixture(autouse=True)
def monitor_test_performance(request):
    """
    Monitor test execution time (function-scoped, auto-use).

    Automatically measures and reports slow tests (>1 second).
    Helps identify performance issues in test suite.
    """
    import time

    start = time.time()
    yield
    duration = time.time() - start

    if duration > 1.0:
        print(f"\n⚠️  SLOW TEST: {request.node.nodeid} took {duration:.2f}s")
        print(f"   Consider marking with @pytest.mark.slow or optimizing")


# ===== Configuration Fixtures =====


@pytest.fixture
def test_settings():
    """
    Provide test configuration settings (function-scoped).

    Returns Settings instance with test-specific configuration.
    """
    return settings


@pytest.fixture
def override_settings(monkeypatch):
    """
    Provide helper to override settings for specific tests (function-scoped).

    Usage:
        def test_with_custom_setting(override_settings):
            override_settings("openai_model", "gpt-3.5-turbo")
            # Test runs with overridden setting
    """
    def _override(key: str, value: Any):
        monkeypatch.setattr(settings, key, value)

    return _override


# ===== Marker Utilities =====


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (require external services)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (full workflow)"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take >1 second"
    )
    config.addinivalue_line(
        "markers", "security: Security-focused tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and load tests"
    )
    config.addinivalue_line(
        "markers", "smoke: Smoke tests for critical paths"
    )
    config.addinivalue_line(
        "markers", "regression: Regression tests"
    )
    config.addinivalue_line(
        "markers", "ci: Tests that run in CI pipeline"
    )
    config.addinivalue_line(
        "markers", "local: Tests that run only locally"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: Tests requiring external API keys"
    )
    config.addinivalue_line(
        "markers", "requires_database: Tests requiring database connection"
    )
    config.addinivalue_line(
        "markers", "requires_redis: Tests requiring Redis connection"
    )


# ===== Test Collection Hooks =====


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers automatically.

    Automatically marks tests based on their location or name patterns.
    """
    for item in items:
        # Add 'unit' marker to tests in tests/unit/
        if "tests/unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Add 'integration' marker to tests in tests/integration/
        if "tests/integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add 'e2e' marker to tests in tests/e2e/
        if "tests/e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

        # Add 'security' marker to tests in tests/security/
        if "tests/security" in str(item.fspath):
            item.add_marker(pytest.mark.security)

        # Add 'performance' marker to tests in tests/performance/
        if "tests/performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
