# HERMES Test Suite

Comprehensive testing infrastructure for HERMES AI Voice Agent System.

**Target Coverage:** 80%+ code coverage across all modules
**Test Framework:** pytest with asyncio support
**Current Status:** Phase 3 Complete - Core fixtures implemented

---

## Quick Start

### Running All Tests

```bash
# Run all tests with coverage report
pytest

# Run specific test categories
pytest -m unit              # Fast unit tests only
pytest -m integration       # Integration tests
pytest -m e2e              # End-to-end tests
pytest -m security         # Security tests
```

### Running Tests in Docker

```bash
# Start development environment with test database
./scripts/docker-start.sh dev

# Run tests in Docker container
docker-compose -f docker-compose.dev.yml exec api pytest

# Run specific test file
docker-compose -f docker-compose.dev.yml exec api pytest tests/test_fixtures_verification.py -v
```

---

## Test Organization

```
tests/
├── conftest.py                      # Root fixtures (25+ shared fixtures)
├── test_fixtures_verification.py   # Fixture validation tests
│
├── unit/                            # Unit tests (fast, isolated)
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
│
├── integration/                     # Integration tests (external services)
│   ├── api/
│   ├── auth_flow/
│   ├── billing_flow/
│   ├── clio_integration/
│   ├── database/
│   ├── lawpay_integration/
│   └── voice_pipeline/
│
├── e2e/                            # End-to-end tests (complete workflows)
│   ├── complete_call_flow/
│   ├── matter_creation/
│   └── user_onboarding/
│
├── performance/                     # Performance & load tests
│   ├── load_tests/
│   ├── stress_tests/
│   └── benchmarks/
│
├── security/                        # Security-focused tests
│   ├── authentication/
│   ├── authorization/
│   ├── input_validation/
│   └── vulnerability_scans/
│
└── fixtures/                        # Additional test fixtures
    ├── __init__.py
    ├── api_fixtures.py
    ├── auth_fixtures.py
    ├── database_fixtures.py
    └── mock_data.py
```

---

## Available Fixtures

All fixtures are defined in `conftest.py` and available to all tests.

### Database Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `test_engine` | session | SQLAlchemy async engine for test database |
| `test_session_factory` | session | Session factory for creating DB sessions |
| `db_session` | function | Database session with automatic rollback |

**Usage:**
```python
async def test_create_user(db_session):
    user = User(email="test@example.com")
    db_session.add(user)
    await db_session.commit()
    assert user.id is not None
```

### Redis Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `redis_client` | function | Redis client with automatic cleanup |

**Usage:**
```python
async def test_cache_data(redis_client):
    await redis_client.set("key", "value")
    result = await redis_client.get("key")
    assert result == "value"
```

### API Client Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `api_client` | function | Synchronous FastAPI TestClient |
| `async_api_client` | function | Asynchronous HTTPX client |

**Usage:**
```python
def test_health_endpoint(api_client):
    response = api_client.get("/health")
    assert response.status_code == 200

async def test_async_endpoint(async_api_client):
    response = await async_api_client.get("/api/v1/matters")
    assert response.status_code == 200
```

### Authentication Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `mock_user` | function | Mock user data dictionary |
| `mock_admin_user` | function | Mock admin user data |
| `jwt_handler` | function | JWT token handler |
| `auth_headers` | function | Auth headers with valid JWT token |
| `admin_auth_headers` | function | Admin auth headers |

**Usage:**
```python
def test_protected_endpoint(api_client, auth_headers):
    response = api_client.get("/api/v1/matters", headers=auth_headers)
    assert response.status_code == 200

def test_admin_endpoint(api_client, admin_auth_headers):
    response = api_client.delete("/api/v1/users/123", headers=admin_auth_headers)
    assert response.status_code == 200
```

### Mock Service Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `mock_openai_client` | function | Mock OpenAI API client |
| `mock_whisper_client` | function | Mock Whisper STT client |
| `mock_kokoro_client` | function | Mock Kokoro TTS client |
| `mock_clio_client` | function | Mock Clio CRM client |
| `mock_stripe_client` | function | Mock Stripe billing client |
| `mock_lawpay_client` | function | Mock LawPay payment client |
| `mock_zapier_client` | function | Mock Zapier webhook client |

**Usage:**
```python
async def test_reasoning_with_mock_openai(mock_openai_client):
    # mock_openai_client is pre-configured with sample responses
    response = await mock_openai_client.chat.completions.create(...)
    assert response.choices[0].message.content is not None
```

### Test Data Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `sample_audio_file` | function | Generated WAV audio file (1s, 440Hz) |
| `sample_legal_matter` | function | Sample legal matter data |
| `sample_client_intake` | function | Sample client intake data |
| `sample_conversation_transcript` | function | Sample HERMES conversation |

**Usage:**
```python
def test_audio_processing(sample_audio_file):
    with open(sample_audio_file, 'rb') as f:
        audio_data = f.read()
    assert len(audio_data) > 0

def test_matter_creation(sample_legal_matter):
    matter = create_matter(**sample_legal_matter)
    assert matter.matter_type == "Personal Injury"
```

### Configuration Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `test_settings` | function | Application settings instance |
| `override_settings` | function | Helper to override settings |

**Usage:**
```python
def test_with_custom_setting(override_settings, test_settings):
    override_settings("openai_model", "gpt-3.5-turbo")
    assert test_settings.openai_model == "gpt-3.5-turbo"
```

---

## Test Markers

Tests are automatically marked based on their location, or you can manually add markers:

```python
import pytest

@pytest.mark.unit
def test_something():
    pass

@pytest.mark.integration
@pytest.mark.requires_database
async def test_database_integration(db_session):
    pass

@pytest.mark.slow
@pytest.mark.performance
def test_load_handling():
    pass
```

### Available Markers

| Marker | Description | Auto-applied |
|--------|-------------|--------------|
| `unit` | Fast, isolated unit tests | tests/unit/ |
| `integration` | Tests requiring external services | tests/integration/ |
| `e2e` | End-to-end workflow tests | tests/e2e/ |
| `security` | Security-focused tests | tests/security/ |
| `performance` | Performance and load tests | tests/performance/ |
| `slow` | Tests taking >1 second | Manual |
| `smoke` | Critical path smoke tests | Manual |
| `regression` | Regression tests | Manual |
| `ci` | Tests running in CI pipeline | Manual |
| `local` | Tests running only locally | Manual |
| `requires_api_key` | Needs external API keys | Manual |
| `requires_database` | Needs database connection | Manual |
| `requires_redis` | Needs Redis connection | Manual |

### Running Tests by Marker

```bash
# Run only unit tests (fast)
pytest -m unit

# Run integration tests
pytest -m integration

# Run all except slow tests
pytest -m "not slow"

# Run security and integration tests
pytest -m "security or integration"

# Skip tests requiring API keys
pytest -m "not requires_api_key"
```

---

## Coverage Reports

### Generating Coverage

```bash
# HTML coverage report
pytest --cov=hermes --cov-report=html

# View in browser
open htmlcov/index.html

# Terminal coverage report
pytest --cov=hermes --cov-report=term-missing

# XML coverage (for CI)
pytest --cov=hermes --cov-report=xml
```

### Coverage Configuration

Coverage is configured in `pytest.ini`:
- **Target:** 80%+ coverage (build fails below this)
- **Branch coverage:** Enabled
- **Omitted:** Tests, venv, migrations, __init__.py, main.py

### Coverage Thresholds

```ini
[coverage:run]
source = hermes
branch = True

[coverage:report]
fail_under = 80
show_missing = True
```

---

## Writing Tests

### Unit Test Example

```python
"""Unit tests for JWT authentication"""
import pytest
from hermes.auth.jwt_handler import JWTHandler
from hermes.auth.models import Role

class TestJWTCreation:
    """Test JWT token creation"""

    def test_create_token_pair(self, jwt_handler, mock_user):
        """Should create valid access and refresh tokens"""
        token_pair = jwt_handler.create_token_pair(
            subject=mock_user["id"],
            tenant_id=mock_user["tenant_id"],
            roles=[Role.ADMIN]
        )

        assert token_pair.access_token is not None
        assert token_pair.refresh_token is not None

        # Verify token can be decoded
        payload = jwt_handler.decode(token_pair.access_token)
        assert payload.sub == mock_user["id"]
        assert payload.type == "access"
```

### Integration Test Example

```python
"""Integration tests for Clio API"""
import pytest

@pytest.mark.integration
@pytest.mark.requires_api_key
class TestClioIntegration:
    """Test Clio CRM integration"""

    async def test_create_matter_flow(
        self,
        db_session,
        mock_clio_client,
        sample_legal_matter
    ):
        """Should create matter in Clio and save to database"""
        # Create matter via Clio API
        clio_matter = await mock_clio_client.create_matter(sample_legal_matter)
        assert clio_matter["id"] is not None

        # Save to database
        db_matter = Matter(**sample_legal_matter, clio_id=clio_matter["id"])
        db_session.add(db_matter)
        await db_session.commit()

        assert db_matter.id is not None
```

### E2E Test Example

```python
"""End-to-end tests for complete call flow"""
import pytest

@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteCallFlow:
    """Test complete client intake call flow"""

    async def test_intake_to_matter_creation(
        self,
        async_api_client,
        auth_headers,
        sample_audio_file,
        mock_openai_client,
        mock_whisper_client,
        mock_clio_client
    ):
        """Should handle complete flow from call to matter creation"""
        # 1. Start voice call
        ws_response = await async_api_client.websocket_connect("/ws/voice")
        # 2. Send audio
        with open(sample_audio_file, 'rb') as f:
            await ws_response.send_bytes(f.read())
        # 3. Receive AI response
        response = await ws_response.receive_json()
        assert response["status"] == "success"
        # 4. Verify matter created
        matters = await async_api_client.get(
            "/api/v1/matters",
            headers=auth_headers
        )
        assert len(matters.json()) > 0
```

---

## Performance Testing

### Benchmarking

```python
import pytest

@pytest.mark.performance
def test_voice_pipeline_latency(benchmark, sample_audio_file):
    """Voice pipeline should complete in <500ms"""
    result = benchmark(process_voice_pipeline, sample_audio_file)
    assert result.duration < 0.5  # 500ms target

@pytest.mark.slow
@pytest.mark.performance
async def test_concurrent_api_calls():
    """Should handle 100+ concurrent API calls"""
    tasks = [make_api_call() for _ in range(100)]
    results = await asyncio.gather(*tasks)
    assert all(r.status_code == 200 for r in results)
```

### Load Testing

```bash
# Run load tests
pytest -m performance tests/performance/load_tests/

# Run stress tests
pytest -m performance tests/performance/stress_tests/
```

---

## Continuous Integration

Tests run automatically in GitHub Actions on:
- Every push to main/develop
- Every pull request
- Nightly (full suite including slow tests)

### CI Configuration

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pytest -m "not slow" --cov=hermes --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### Local CI Simulation

```bash
# Run the same tests as CI
pytest -m "not slow and not requires_api_key" --cov=hermes --cov-fail-under=80
```

---

## Troubleshooting

### Database Connection Issues

```bash
# Start test database in Docker
./scripts/docker-start.sh dev

# Verify database is accessible
docker-compose -f docker-compose.dev.yml exec postgres-test pg_isready -U postgres
```

### Redis Connection Issues

```bash
# Verify Redis is accessible
docker-compose -f docker-compose.dev.yml exec redis redis-cli ping
```

### Slow Tests

```bash
# Identify slow tests
pytest --durations=10

# Tests >1s are automatically flagged
# Consider marking with @pytest.mark.slow
```

### Import Errors

```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH=/home/user/hermes-agent:$PYTHONPATH

# Or install in development mode
pip install -e .
```

---

## Best Practices

### ✅ DO

- **Write tests first** (TDD approach)
- **Use fixtures** for reusable test data
- **Mock external services** (OpenAI, Clio, Stripe, etc.)
- **Test edge cases** and error conditions
- **Keep tests fast** (<1s for unit tests)
- **Use descriptive names** (`test_create_matter_with_invalid_email`)
- **One assertion concept per test**
- **Clean up after tests** (fixtures handle this automatically)

### ❌ DON'T

- **Don't use production API keys** in tests
- **Don't make real API calls** (use mocks)
- **Don't share state** between tests
- **Don't skip cleanup** (causes test pollution)
- **Don't test implementation details** (test behavior)
- **Don't write flaky tests** (random failures)
- **Don't commit failing tests**

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [HERMES Claude Guidelines](../CLAUDE.md)

---

## Next Steps

### Planned Implementations (Phases 4-14)

- [ ] **Phase 4:** Unit tests for all core modules (300+ tests)
- [ ] **Phase 5:** Integration tests (100+ tests)
- [ ] **Phase 6:** End-to-end tests (35+ tests)
- [ ] **Phase 7:** Performance & load tests (30+ tests)
- [ ] **Phase 8:** Security tests (50+ tests)
- [ ] **Phase 9:** Additional fixtures & utilities
- [ ] **Phase 10:** Mock service improvements
- [ ] **Phase 11:** Test data generators
- [ ] **Phase 12:** CI/CD integration enhancements
- [ ] **Phase 13:** Code quality tools (mypy, black, flake8)
- [ ] **Phase 14:** Final documentation & examples

---

**Last Updated:** 2025-11-17
**Maintainer:** HERMES Development Team
**Status:** Phase 3 Complete - Core Infrastructure Ready
