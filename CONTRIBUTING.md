# Contributing to HERMES

Welcome to HERMES! We're excited that you're interested in contributing to our AI-powered voice agent system for law firms.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Type Hints Requirements](#type-hints-requirements)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Security Considerations](#security-considerations)
- [Legal & Compliance](#legal--compliance)

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- Docker (optional, for containerized development)

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/clduab11/hermes-agent.git
   cd hermes-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

6. **Verify setup**
   ```bash
   pytest
   python -m hermes.main
   ```

### Docker Setup (Optional)

```bash
docker-compose -f docker-compose.dev.yml up
```

## Development Workflow

### Branch Naming

| Type | Format | Example |
|------|--------|---------|
| Features | `feature/short-description` | `feature/clio-oauth-integration` |
| Bug fixes | `bugfix/short-description` | `bugfix/token-refresh-race` |
| Hotfixes | `hotfix/short-description` | `hotfix/voice-latency-spike` |
| Refactoring | `refactor/short-description` | `refactor/voice-pipeline-cleanup` |
| Documentation | `docs/short-description` | `docs/api-examples` |

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: feat, fix, docs, style, refactor, perf, test, chore

**Example**:
```
feat(voice): implement VAD for natural turn-taking

Added Voice Activity Detection using WebRTC VAD to detect when
the user has finished speaking, enabling more natural conversation
flow without explicit turn-taking signals.

Closes #42
```

### Running Quality Checks

```bash
# Run all checks locally
black .                     # Format code
isort .                     # Sort imports
flake8 hermes tests         # Lint code
mypy hermes                 # Type check
pytest                      # Run tests

# Or use pre-commit
pre-commit run --all-files
```

## Code Style Guidelines

### Python Standards

- **PEP 8 compliant** with Black formatting (88 char line length)
- **Type hints** for all functions (MyPy strict mode)
- **Docstrings** for public APIs (Google style)
- **Async/await** for all I/O operations

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Functions & Variables | `snake_case` | `create_matter()` |
| Classes | `PascalCase` | `VoicePipelineManager` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRY_ATTEMPTS` |
| Private Methods | `_snake_case` | `_internal_method()` |

### Configuration

See `pyproject.toml` for tool configurations:
- Black: line-length 88
- isort: profile "black"
- flake8: extends E203, W503
- MyPy: strict mode enabled

## Testing Requirements

### Coverage Requirements

- **Overall coverage**: >= 80%
- **Critical modules** (auth, billing, security): >= 95%
- **All new code** requires tests

### Test Types

- **Unit tests**: Business logic in isolation
- **Integration tests**: API endpoints, database operations
- **E2E tests**: Critical user workflows

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=hermes --cov-report=html

# Specific markers
pytest -m unit
pytest -m integration
pytest -m "not e2e"
```

### Test Structure

```python
import pytest

@pytest.mark.unit
async def test_matter_creation():
    """Test creating a new legal matter."""
    # Arrange
    client_data = {...}

    # Act
    result = await create_matter(client_data)

    # Assert
    assert result.id is not None
    assert result.status == "Open"
```

## Type Hints Requirements

### Requirements

- All functions must have type hints for parameters and return values
- Use `typing` module for complex types
- MyPy strict mode must pass
- Avoid `Any` unless absolutely necessary

### Example

```python
from typing import Optional, Any

async def create_matter(
    client_name: str,
    matter_type: str,
    jurisdiction: str,
    description: Optional[str] = None
) -> dict[str, Any]:
    """Create a new legal matter."""
    ...
```

### Running Type Checks

```bash
mypy hermes --config-file pyproject.toml
```

## Documentation

### Code Documentation

- **Docstrings**: Required for all public functions/classes
- **Comments**: For complex logic only
- **Type hints**: Serve as documentation

### API Documentation

- Update docstrings for changed functions
- Update OpenAPI specs for API changes
- Update README.md for new features

## Pull Request Process

1. **Create feature branch** from main/develop
2. **Make changes** following guidelines
3. **Run all checks** locally
4. **Create PR** using template
5. **Request review** from maintainers
6. **Address feedback**
7. **Merge** after approval

### PR Requirements

- [ ] All CI checks pass
- [ ] Tests added for new code
- [ ] Documentation updated
- [ ] PR template completed
- [ ] Linked to related issues

## Security Considerations

### Never Commit

- API keys or secrets
- Passwords or tokens
- Personal data
- Production credentials

### Always Do

- Use environment variables for secrets
- Validate all user inputs
- Follow OWASP guidelines
- Report security issues privately

### Reporting Security Issues

Email: security@parallax-ai.app

Do NOT create public issues for security vulnerabilities.

## Legal & Compliance

### Important Notes

- This is legal tech software - compliance is critical
- Never provide legal advice in code or comments
- Maintain attorney-client privilege protection
- Follow audit logging requirements
- Reference `docs/legal-compliance.md` for guidelines

### Data Handling

- Encrypt sensitive data at rest and in transit
- Implement proper data retention
- Support GDPR deletion requests
- Log all access to privileged data

## Getting Help

- Check existing issues and documentation
- Ask questions in GitHub Discussions
- Contact maintainer: @clduab11

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Highlighted in release notes

---

Thank you for contributing to HERMES!
