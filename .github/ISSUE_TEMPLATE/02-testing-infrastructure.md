---
name: "Testing Infrastructure"
about: "Track testing infrastructure improvements for HERMES"
title: "[TEST] Testing Infrastructure Enhancement"
labels: ["testing", "quality", "technical-debt"]
assignees: ["clduab11"]
---

## Objective

Achieve and maintain 80%+ code coverage with comprehensive test suite covering unit, integration, E2E, security, and performance testing.

## Current State

- pytest configured in `pyproject.toml` with 80% target
- CI only enforces 15% coverage (see `.github/workflows/consolidated-ci.yml` line 120)
- 20 test files exist but many modules lack coverage
- Development testing tools commented out in `requirements.txt` (lines 58-67)

## Tasks

### Phase 1: Infrastructure Setup

- [ ] Uncomment and update testing dependencies in `requirements.txt`
  - pytest==7.4.4
  - pytest-asyncio==0.23.3
  - pytest-cov==4.1.0
  - coverage[toml]==7.4.1

- [ ] Update `requirements-ci.txt` to include all testing tools

- [ ] Increase coverage threshold in `.github/workflows/consolidated-ci.yml`
  - Change line 120: `--cov-fail-under=15` to `--cov-fail-under=80`
  - Make coverage check blocking (remove `|| echo` fallback)

- [ ] Add pytest-xdist for parallel test execution
- [ ] Add hypothesis for property-based testing

### Phase 2: Unit Test Coverage

Add missing unit tests for modules without coverage:

**Analytics & Monitoring**
- [ ] `hermes/analytics/engine.py`
- [ ] `hermes/monitoring/*.py` (3 files)

**API Endpoints**
- [ ] `hermes/api/*.py` (10+ files need tests)

**Automation**
- [ ] `hermes/automation/*.py` (2 files)

**Cache & Database**
- [ ] `hermes/cache/tenant_cache_manager.py`
- [ ] `hermes/database/*.py` (5 files)

**Integrations**
- [ ] `hermes/integrations/clio/*.py`
- [ ] `hermes/integrations/lawpay/*.py`

**Knowledge & MCP**
- [ ] `hermes/knowledge/graph_sync.py`
- [ ] `hermes/mcp/*.py` (4 files)

**Security & Middleware**
- [ ] `hermes/middleware/security.py`
- [ ] `hermes/security/*.py` (11 files)

**Services & Scaling**
- [ ] `hermes/services/*.py` (3 files)
- [ ] `hermes/scaling/auto_scaler.py`
- [ ] `hermes/optimization/memory_manager.py`

**Tenancy**
- [ ] `hermes/tenancy/isolation_manager.py`

**TTS & Voice**
- [ ] `hermes/tts/*.py` (factory, interface, kokoro)
- [ ] `hermes/voice/*.py` (context_manager, legal_nlp, multilang_support)

**Utilities**
- [ ] `hermes/utils/rate_limiting.py`

### Phase 3: Integration Tests

- [ ] Add integration tests for database operations with test fixtures
- [ ] Add integration tests for external services
  - Clio CRM integration
  - LawPay integration
  - Stripe integration
  - Zapier webhooks
- [ ] Add WebSocket integration tests (reference: `tests/test_voice_pipeline.py`)
- [ ] Add API endpoint integration tests for all routers

### Phase 4: E2E Tests

- [ ] Enhance `tests/e2e_test_suite.py` with complete user workflows
- [ ] Add E2E tests for voice processing pipeline
- [ ] Add E2E tests for authentication and authorization flows
- [ ] Add E2E tests for billing and subscription workflows
- [ ] Add E2E tests for matter intake workflow

### Phase 5: Security & Performance Tests

**Security Tests**
- [ ] Authentication bypass attempts
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] Rate limiting effectiveness
- [ ] API key validation
- [ ] JWT token security

**Performance Tests**
- [ ] Load tests for voice processing pipeline
- [ ] Performance benchmarks for critical paths
- [ ] Enhance `tests/performance/test_benchmarks.py`
- [ ] Database query performance
- [ ] WebSocket connection scaling

### Phase 6: Test Infrastructure

- [ ] Create comprehensive `tests/conftest.py` with shared fixtures
  - Database fixtures (test PostgreSQL)
  - Redis fixtures (test Redis)
  - Mock service fixtures (Clio, LawPay, OpenAI)
  - Authentication fixtures (test users, API keys)

- [ ] Add test data factories using factory_boy
- [ ] Add test utilities for common assertions
- [ ] Add coverage reporting to CI with HTML artifacts
- [ ] Add mutation testing with mutmut to verify test quality

## Acceptance Criteria

- [ ] Overall code coverage >= 80%
- [ ] Critical modules (auth, billing, security) >= 95%
- [ ] All new code requires tests (enforced in CI)
- [ ] CI fails if coverage drops below 80%
- [ ] Test suite runs in under 5 minutes
- [ ] All tests are deterministic (no flaky tests)
- [ ] Test failures provide clear, actionable error messages

## Technical References

- Configuration: `pyproject.toml`
- CI Workflow: `.github/workflows/consolidated-ci.yml`
- Existing Tests: `tests/` directory
- Dependencies: `requirements.txt`, `requirements-ci.txt`

## Notes

- Use pytest fixtures extensively for test isolation
- Mock external services in unit tests
- Use real services (with test accounts) for integration tests
- Consider test database seeding for consistent test data
