---
name: "Type Hint Coverage"
about: "Track type hint coverage improvements for HERMES"
title: "[TYPE] Type Hint Coverage Enhancement"
labels: ["type-safety", "quality", "technical-debt"]
assignees: ["clduab11"]
---

## Objective

Achieve 100% type hint coverage with MyPy strict mode enabled to catch type errors at development time and improve code maintainability.

## Current State

- MyPy configured in `pyproject.toml` but NOT in strict mode
- `disallow_untyped_defs = false` (line 58)
- `disallow_incomplete_defs = false` (line 59)
- No MyPy enforcement in CI workflows
- Many modules lack comprehensive type hints

## Tasks

### Phase 1: Enable Strict Mode Progressively

- [ ] Update `pyproject.toml` [tool.mypy] section:
  - Set `disallow_untyped_defs = true`
  - Set `disallow_incomplete_defs = true`
  - Set `disallow_untyped_calls = true`
  - Set `disallow_untyped_decorators = true`
  - Set `strict_optional = true`
  - Set `disallow_any_generics = true`
  - Keep `warn_return_any = true` (already enabled)

- [ ] Add MyPy to CI workflow in `.github/workflows/consolidated-ci.yml`
  - Add as required check (blocking)
  - Cache MyPy cache directory

- [ ] Use per-module overrides for gradual adoption

### Phase 2: Core Module Type Hints

- [ ] `hermes/main.py` - FastAPI application and endpoints
- [ ] `hermes/config.py` - Settings and configuration
- [ ] `hermes/voice_pipeline.py` - Voice processing pipeline
- [ ] `hermes/speech_to_text.py` - STT components
- [ ] `hermes/text_to_speech.py` - TTS components
- [ ] `hermes/websocket_handler.py` - WebSocket handling
- [ ] `hermes/event_streaming.py` - Event streaming service

### Phase 3: Authentication & Security

- [ ] `hermes/auth/*.py` (6 files)
  - JWT handling
  - RBAC implementation
  - Middleware
  - Models
  - API key auth
  - Session management

- [ ] `hermes/security/*.py` (11 files)
  - All security modules
  - Encryption utilities
  - Audit logging

- [ ] `hermes/middleware/security.py`

### Phase 4: Database & Data Layer

- [ ] `hermes/database/*.py` (5 files)
  - Connection management
  - Models
  - Security
  - Migrations

- [ ] `hermes/cache/tenant_cache_manager.py`
- [ ] `hermes/tenancy/isolation_manager.py`

### Phase 5: API & Services

- [ ] `hermes/api/*.py` (10 files)
  - All API endpoint modules
  - Request/response models

- [ ] `hermes/services/*.py` (3 files)
- [ ] `hermes/integrations/**/*.py`
  - Clio integration
  - LawPay integration
  - Zapier integration
  - Stripe integration

### Phase 6: Supporting Modules

- [ ] `hermes/analytics/engine.py`
- [ ] `hermes/billing/*.py` (2 files)
- [ ] `hermes/monitoring/*.py` (3 files)
- [ ] `hermes/mcp/*.py` (4 files)
- [ ] `hermes/reasoning/*.py` (3 files)
- [ ] `hermes/resilience/*.py` (2 files)
- [ ] `hermes/scaling/auto_scaler.py`
- [ ] `hermes/optimization/memory_manager.py`
- [ ] `hermes/tts/*.py` (3 files)
- [ ] `hermes/voice/*.py` (3 files)
- [ ] `hermes/utils/*.py`
- [ ] `hermes/automation/*.py` (2 files)
- [ ] `hermes/knowledge/graph_sync.py`
- [ ] `hermes/audit/api.py`
- [ ] `hermes/auxiliary_services.py`

### Phase 7: Type Stubs & Third-Party

- [ ] Create type stubs for untyped dependencies
- [ ] Update `[[tool.mypy.overrides]]` for third-party libraries
- [ ] Add `types-*` packages:
  - types-requests
  - types-redis
  - types-PyYAML
  - Other as needed

### Phase 8: CI Integration

- [ ] Add MyPy check to CI workflow (before tests)
- [ ] Make MyPy failures block PRs
- [ ] Add MyPy cache to CI caching strategy
- [ ] Generate MyPy coverage report and track progress

## Acceptance Criteria

- [ ] 100% of functions and methods have type hints for parameters and return values
- [ ] MyPy strict mode enabled globally
- [ ] No per-module exceptions (except third-party overrides)
- [ ] MyPy passes with zero errors in CI
- [ ] All new code must pass MyPy strict checks
- [ ] Type hints are accurate and meaningful (not just `Any` everywhere)

## Tools & Resources

- MyPy documentation: https://mypy.readthedocs.io/
- Check status: `mypy --strict hermes/`
- Generate report: `mypy --html-report mypy-report hermes/`
- Auto-generate hints: Consider using `monkeytype` for runtime traces

## Technical References

- Configuration: `pyproject.toml` (lines 54-77)
- CI Workflow: `.github/workflows/consolidated-ci.yml`
- All Python files in `hermes/` directory

## Notes

- Gradual rollout prevents overwhelming changes
- Focus on public APIs first
- Use `typing` module for complex types
- Document why `Any` is used when unavoidable
- Consider using Protocol classes for duck typing
