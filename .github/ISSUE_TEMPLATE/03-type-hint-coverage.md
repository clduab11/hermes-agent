---
name: "[MILESTONE 3] 100% Type Hint Coverage & MyPy Strict"
about: Achieve 100% type hint coverage and pass MyPy strict validation
title: "[MILESTONE 3] 100% Type Hint Coverage & MyPy Strict"
labels: code-quality, type-hints, medium-priority, copilot-ready
assignees: ''
---

## 🎯 Objective

Achieve 100% type hint coverage across the codebase and pass MyPy strict mode validation. This improves code maintainability, IDE support, and catches bugs at development time per CLAUDE.md requirements.

**Current Status:** 62.6% - 696 out of 1,112 functions have type hints
**Target Status:** 100% - All functions have complete type hints, MyPy strict passes
**Completion Criteria:** All functions typed, MyPy strict mode passes, CI/CD enforces type checking

---

## 📋 Prerequisites

- Python 3.11+
- MyPy installed
- Understanding of Python typing module
- Familiarity with HERMES codebase structure

---

## ✅ Acceptance Criteria

- [ ] 100% of functions have parameter type hints
- [ ] 100% of functions have return type hints
- [ ] All class attributes are typed
- [ ] Complex types use TypedDict/Protocol where appropriate
- [ ] MyPy passes in strict mode with zero errors
- [ ] Custom types documented in `hermes/types.py`
- [ ] CI/CD enforces type checking
- [ ] Documentation updated with type hint examples

---

## 📝 Step-by-Step Implementation Guide

### PHASE 1: Audit Current Type Hint Status

**Create audit script to identify missing type hints:**

**File:** `scripts/audit_type_hints.py`

```python
#!/usr/bin/env python3
"""
Audit script to find functions without type hints.
"""
import ast
import os
from pathlib import Path
from typing import List, Tuple


class TypeHintAuditor(ast.NodeVisitor):
    """AST visitor to check for type hints."""

    def __init__(self, filename: str):
        self.filename = filename
        self.missing_hints: List[Tuple[str, int, str]] = []
        self.total_functions = 0
        self.typed_functions = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions."""
        self.total_functions += 1

        # Check if function has return type hint
        has_return_hint = node.returns is not None

        # Check if all parameters have type hints (except self, cls)
        params_to_check = [
            arg for arg in node.args.args
            if arg.arg not in ('self', 'cls')
        ]
        has_param_hints = all(arg.annotation is not None for arg in params_to_check)

        if has_return_hint and (has_param_hints or not params_to_check):
            self.typed_functions += 1
        else:
            reason = []
            if not has_return_hint:
                reason.append("missing return type")
            if not has_param_hints and params_to_check:
                reason.append("missing parameter types")

            self.missing_hints.append((
                node.name,
                node.lineno,
                ", ".join(reason)
            ))

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definitions."""
        self.visit_FunctionDef(node)


def audit_file(filepath: Path) -> Tuple[int, int, List[Tuple[str, int, str]]]:
    """Audit a single Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        auditor = TypeHintAuditor(str(filepath))
        auditor.visit(tree)

        return auditor.total_functions, auditor.typed_functions, auditor.missing_hints
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return 0, 0, []


def main():
    """Run audit on hermes/ directory."""
    hermes_dir = Path(__file__).parent.parent / "hermes"

    total_funcs = 0
    typed_funcs = 0
    files_with_issues = []

    print("Auditing type hints in HERMES codebase...\n")
    print("=" * 80)

    for py_file in hermes_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue

        total, typed, missing = audit_file(py_file)

        if total > 0:
            total_funcs += total
            typed_funcs += typed

            if missing:
                rel_path = py_file.relative_to(hermes_dir.parent)
                files_with_issues.append((rel_path, total, typed, missing))

    # Print summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Total functions: {total_funcs}")
    print(f"Typed functions: {typed_funcs}")
    print(f"Missing type hints: {total_funcs - typed_funcs}")
    print(f"Coverage: {typed_funcs / total_funcs * 100:.1f}%")
    print(f"\n{'='*80}")

    # Print files with issues
    if files_with_issues:
        print(f"\nFILES NEEDING TYPE HINTS ({len(files_with_issues)} files):")
        print(f"{'='*80}\n")

        # Sort by number of missing hints
        files_with_issues.sort(key=lambda x: len(x[3]), reverse=True)

        for filepath, total, typed, missing in files_with_issues:
            coverage = typed / total * 100 if total > 0 else 0
            print(f"{filepath}")
            print(f"  Coverage: {coverage:.1f}% ({typed}/{total} functions)")
            print(f"  Missing hints in {len(missing)} function(s):")

            for func_name, lineno, reason in missing[:5]:  # Show first 5
                print(f"    - {func_name}() at line {lineno}: {reason}")

            if len(missing) > 5:
                print(f"    ... and {len(missing) - 5} more")

            print()


if __name__ == "__main__":
    main()
```

**Tasks:**

- [ ] Create `scripts/audit_type_hints.py`
- [ ] Make executable: `chmod +x scripts/audit_type_hints.py`
- [ ] Run audit: `python scripts/audit_type_hints.py`
- [ ] Save output to `TYPE_HINTS_AUDIT.md` for tracking
- [ ] Create prioritized list of files to fix

**Example Output:**
```
SUMMARY
================================================================================
Total functions: 1,112
Typed functions: 696
Missing type hints: 416
Coverage: 62.6%

FILES NEEDING TYPE HINTS (43 files):
================================================================================

hermes/api/v1/matters.py
  Coverage: 45.0% (9/20 functions)
  Missing hints in 11 function(s):
    - get_matters() at line 45: missing return type
    - create_matter() at line 78: missing parameter types
    ...
```

---

### PHASE 2: Configure MyPy Strict Mode

**File:** `pyproject.toml` (Update existing)

```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_optional = true
strict_equality = true
check_untyped_defs = true
disallow_any_generics = true
disallow_subclassing_any = true
disallow_untyped_calls = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_return_any = true
warn_unused_ignores = true
show_error_codes = true
show_column_numbers = true
pretty = true

# Per-module options for gradual typing
[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false  # Tests can be less strict initially

[[tool.mypy.overrides]]
module = "alembic.*"
ignore_errors = true  # Ignore migration files

# External libraries without stubs
[[tool.mypy.overrides]]
module = [
    "supabase.*",
    "mem0.*",
    "kokoro.*"
]
ignore_missing_imports = true
```

**File:** Create `.mypy.ini` (optional, for more control)

```ini
[mypy]
python_version = 3.11
strict = true
warn_return_any = true
warn_unused_configs = true
show_error_codes = true

[mypy-tests.*]
disallow_untyped_defs = false

[mypy-alembic.*]
ignore_errors = true
```

**Tasks:**
- [ ] Update `pyproject.toml` with strict MyPy configuration
- [ ] Run MyPy to see initial errors: `mypy hermes/`
- [ ] Document number of errors as baseline
- [ ] Create `mypy-errors-baseline.txt` for tracking

---

### PHASE 3: Create Custom Types Module

**File:** `hermes/types.py`

```python
"""
Custom type definitions for HERMES.

This module contains TypedDict classes, Protocols, and type aliases
used throughout the HERMES codebase.
"""
from typing import TypedDict, Protocol, Literal, Union, Any
from datetime import datetime
from uuid import UUID


# ============================================================================
# Voice Pipeline Types
# ============================================================================

class TranscriptionResult(TypedDict):
    """Result from speech-to-text transcription."""
    text: str
    confidence: float
    language: str
    duration_ms: int


class TTSResult(TypedDict):
    """Result from text-to-speech synthesis."""
    audio_data: bytes
    format: Literal["wav", "mp3", "opus"]
    duration_ms: int
    sample_rate: int


class VoiceMetrics(TypedDict, total=False):
    """Metrics for voice processing pipeline."""
    stt_latency_ms: int
    llm_latency_ms: int
    tts_latency_ms: int
    total_latency_ms: int
    audio_duration_ms: int
    processing_speed_ratio: float


# ============================================================================
# AI Reasoning Types
# ============================================================================

class ReasoningPathDict(TypedDict):
    """Dictionary representation of a reasoning path."""
    reasoning: str
    response: str
    confidence: float
    path_index: int


class PathEvaluationDict(TypedDict):
    """Dictionary representation of path evaluation."""
    path_index: int
    score: float
    reasoning_quality: float
    confidence_score: float
    consistency_score: float


class MonteCarloResult(TypedDict):
    """Result from Monte Carlo simulation."""
    confidence: float
    variance: float
    mean_score: float
    simulations: list[dict[str, Any]]
    num_simulations: int


# ============================================================================
# Integration Types
# ============================================================================

class ClioTokenDict(TypedDict):
    """Clio OAuth tokens."""
    access_token: str
    refresh_token: str
    expires_at: int
    token_type: str


class ClioContactDict(TypedDict, total=False):
    """Clio contact data."""
    id: int
    first_name: str
    last_name: str
    name: str
    email: str
    phone: str
    company: str


class ClioMatterDict(TypedDict, total=False):
    """Clio matter data."""
    id: int
    client_id: int
    description: str
    practice_area: str
    status: Literal["Open", "Pending", "Closed"]
    open_date: str
    close_date: str | None


class LawPayPaymentDict(TypedDict, total=False):
    """LawPay payment data."""
    id: str
    amount: int
    currency: str
    status: Literal["pending", "succeeded", "failed"]
    payment_type: Literal["operating", "trust"]
    description: str
    client_id: str


# ============================================================================
# Authentication Types
# ============================================================================

class TokenPayload(TypedDict):
    """JWT token payload."""
    sub: str  # User ID
    tenant_id: str
    role: str
    exp: int
    iat: int
    type: Literal["access", "refresh"]


class UserCredentials(TypedDict):
    """User login credentials."""
    email: str
    password: str


# ============================================================================
# API Response Types
# ============================================================================

class APIResponse(TypedDict, total=False):
    """Standard API response structure."""
    success: bool
    data: Any
    error: str | None
    message: str | None
    metadata: dict[str, Any]


class PaginatedResponse(TypedDict):
    """Paginated API response."""
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Database Types
# ============================================================================

class TenantDict(TypedDict):
    """Tenant data."""
    id: UUID
    name: str
    domain: str
    status: Literal["active", "suspended", "deleted"]
    created_at: datetime
    settings: dict[str, Any]


# ============================================================================
# Protocols (Structural Typing)
# ============================================================================

class STTProvider(Protocol):
    """Protocol for Speech-to-Text providers."""

    async def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        """Transcribe audio to text."""
        ...

    async def initialize(self) -> None:
        """Initialize the STT provider."""
        ...


class TTSProvider(Protocol):
    """Protocol for Text-to-Speech providers."""

    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        language: str | None = None
    ) -> TTSResult:
        """Synthesize text to speech."""
        ...

    async def initialize(self) -> None:
        """Initialize the TTS provider."""
        ...


class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7
    ) -> str:
        """Generate text from prompt."""
        ...


# ============================================================================
# Type Aliases
# ============================================================================

# Common type aliases
JSON = dict[str, Any]
Headers = dict[str, str]
QueryParams = dict[str, str | int | bool]

# ID types
ClientID = str | int
MatterID = str | int
UserID = UUID | str
TenantID = UUID | str

# Status types
MatterStatus = Literal["Open", "Pending", "Closed"]
PaymentStatus = Literal["pending", "succeeded", "failed", "refunded"]
UserRole = Literal["admin", "attorney", "staff", "client"]
```

**Tasks:**
- [ ] Create `hermes/types.py` with common types
- [ ] Add more TypedDict classes as needed
- [ ] Add Protocol classes for interfaces
- [ ] Document each type with examples

---

### PHASE 4: Add Type Hints to Core Modules (Priority 1)

**Module:** `hermes/voice_pipeline.py`

**Review existing code and add missing type hints:**

```python
# BEFORE (example)
async def process_voice_interaction(self, session_id, audio_data):
    ...

# AFTER
from typing import Optional
from hermes.types import VoiceMetrics, TranscriptionResult

async def process_voice_interaction(
    self,
    session_id: str,
    audio_data: bytes,
    language: Optional[str] = None
) -> VoiceInteraction:
    """
    Process a voice interaction through the complete pipeline.

    Args:
        session_id: Unique identifier for the conversation session
        audio_data: Raw audio bytes (WAV format)
        language: Optional language code (e.g., 'en', 'es')

    Returns:
        VoiceInteraction object with transcription, response, and audio

    Raises:
        ValueError: If audio_data is empty
        STTError: If speech-to-text fails
        LLMError: If LLM generation fails
        TTSError: If text-to-speech fails
    """
    ...
```

**Systematic approach for each function:**

1. Add imports for typing constructs
2. Add parameter type hints
3. Add return type hint
4. Use `Optional[T]` for optional parameters
5. Use `Union[T1, T2]` or `T1 | T2` for multiple types
6. Use custom types from `hermes.types` where applicable
7. Add docstring with Args, Returns, Raises

**Tasks:**

- [ ] Add type hints to `hermes/voice_pipeline.py`
  - [ ] All function parameters
  - [ ] All return types
  - [ ] Class attributes
  - [ ] Run MyPy: `mypy hermes/voice_pipeline.py`
  - [ ] Fix all errors

- [ ] Add type hints to `hermes/main.py`
  - [ ] All FastAPI route handlers
  - [ ] Dependency injection functions
  - [ ] Run MyPy on file

- [ ] Add type hints to `hermes/config.py`
  - [ ] All settings properties
  - [ ] Validation methods
  - [ ] Run MyPy on file

---

### PHASE 5: Add Type Hints to Services (Priority 2)

**Files to update:**
- `hermes/services/*.py`

**Example:** `hermes/services/matter_service.py`

```python
from typing import Optional, List
from uuid import UUID

from hermes.database.models import Matter
from hermes.types import ClioMatterDict, MatterID, TenantID


class MatterService:
    """Service for managing legal matters."""

    async def create_matter(
        self,
        tenant_id: TenantID,
        client_id: ClientID,
        matter_data: ClioMatterDict,
        user_id: UserID
    ) -> Matter:
        """
        Create a new matter.

        Args:
            tenant_id: ID of the tenant
            client_id: ID of the client
            matter_data: Matter data from Clio
            user_id: ID of user creating the matter

        Returns:
            Created Matter instance

        Raises:
            ValueError: If matter_data is invalid
            DatabaseError: If database operation fails
        """
        ...

    async def get_matters(
        self,
        tenant_id: TenantID,
        status: Optional[MatterStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Matter]:
        """Get matters for a tenant with optional filtering."""
        ...

    async def update_matter_status(
        self,
        matter_id: MatterID,
        tenant_id: TenantID,
        new_status: MatterStatus
    ) -> Matter:
        """Update matter status."""
        ...
```

**Tasks:**

- [ ] Add type hints to all files in `hermes/services/`
- [ ] Use custom types from `hermes/types.py`
- [ ] Run MyPy on services: `mypy hermes/services/`
- [ ] Fix all errors

---

### PHASE 6: Add Type Hints to Integrations (Priority 3)

**Files to update:**
- `hermes/integrations/clio/*.py`
- `hermes/integrations/lawpay/*.py`
- `hermes/integrations/zapier/*.py`
- `hermes/integrations/mem0/*.py`

**Example:** `hermes/integrations/clio/client.py`

```python
from typing import Optional, List, Dict, Any
import httpx

from hermes.types import ClioTokenDict, ClioContactDict, ClioMatterDict
from hermes.integrations.clio.auth import ClioTokens


class ClioClient:
    """Client for Clio CRM API."""

    def __init__(
        self,
        base_url: str = "https://app.clio.com/api/v4",
        timeout: float = 30.0
    ) -> None:
        """Initialize Clio client."""
        self.base_url = base_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        tokens: ClioTokens,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Clio API."""
        ...

    async def create_contact(
        self,
        tokens: ClioTokens,
        contact_data: ClioContactDict
    ) -> ClioContactDict:
        """Create a contact in Clio."""
        ...

    async def get_contact(
        self,
        tokens: ClioTokens,
        contact_id: int
    ) -> Optional[ClioContactDict]:
        """Get a contact by ID."""
        ...

    async def create_matter(
        self,
        tokens: ClioTokens,
        matter_data: ClioMatterDict
    ) -> ClioMatterDict:
        """Create a matter in Clio."""
        ...
```

**Tasks:**

- [ ] Add type hints to Clio integration
  - [ ] `hermes/integrations/clio/client.py`
  - [ ] `hermes/integrations/clio/auth.py`
  - [ ] Run MyPy: `mypy hermes/integrations/clio/`

- [ ] Add type hints to LawPay integration
  - [ ] `hermes/integrations/lawpay/client.py`
  - [ ] Run MyPy: `mypy hermes/integrations/lawpay/`

- [ ] Add type hints to Zapier integration
  - [ ] `hermes/integrations/zapier/webhooks.py`
  - [ ] Run MyPy: `mypy hermes/integrations/zapier/`

- [ ] Add type hints to Mem0 integration
  - [ ] `hermes/integrations/mem0/*.py`
  - [ ] Run MyPy

---

### PHASE 7: Add Type Hints to AI/Reasoning (Priority 3)

**Files:**
- `hermes/reasoning/tree_of_thought.py`
- `hermes/reasoning/monte_carlo.py`
- `hermes/knowledge/graph_sync.py`

**Example:** `hermes/reasoning/tree_of_thought.py`

```python
from typing import List, Optional
from dataclasses import dataclass

from hermes.types import ReasoningPathDict, PathEvaluationDict


@dataclass
class ReasoningPath:
    """A single reasoning path in Tree of Thought."""
    reasoning: str
    response: str
    confidence: float
    path_index: int = 0

    def to_dict(self) -> ReasoningPathDict:
        """Convert to dictionary."""
        return {
            "reasoning": self.reasoning,
            "response": self.response,
            "confidence": self.confidence,
            "path_index": self.path_index
        }


class TreeOfThoughtReasoner:
    """Tree of Thought reasoning engine."""

    def __init__(
        self,
        num_paths: int = 3,
        evaluation_model: str = "anthropic/claude-3-sonnet"
    ) -> None:
        """Initialize ToT reasoner."""
        self.num_paths = num_paths
        self.evaluation_model = evaluation_model

    async def generate_paths(
        self,
        query: str,
        system_prompt: Optional[str] = None
    ) -> List[ReasoningPath]:
        """Generate multiple reasoning paths."""
        ...

    async def evaluate_paths(
        self,
        paths: List[ReasoningPath]
    ) -> List[PathEvaluation]:
        """Evaluate quality of reasoning paths."""
        ...

    def select_best_path(
        self,
        evaluations: List[PathEvaluation]
    ) -> int:
        """Select index of best path based on evaluations."""
        ...

    async def reason(
        self,
        query: str,
        system_prompt: Optional[str] = None
    ) -> ReasoningPath:
        """Complete ToT reasoning flow."""
        ...
```

**Tasks:**

- [ ] Add type hints to `hermes/reasoning/tree_of_thought.py`
- [ ] Add type hints to `hermes/reasoning/monte_carlo.py`
- [ ] Add type hints to `hermes/knowledge/graph_sync.py`
- [ ] Run MyPy: `mypy hermes/reasoning/ hermes/knowledge/`

---

### PHASE 8: Add Type Hints to Auth & Security (Priority 3)

**Files:**
- `hermes/auth/*.py`
- `hermes/security/*.py`
- `hermes/middleware/*.py`

**Example:** `hermes/auth/jwt_handler.py`

```python
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import jwt

from hermes.types import TokenPayload, UserID, TenantID
from hermes.config import get_settings


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.

    Args:
        data: Payload data to encode
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    ...


def create_refresh_token(
    user_id: UserID,
    tenant_id: TenantID
) -> str:
    """Create JWT refresh token."""
    ...


def decode_token(token: str) -> TokenPayload:
    """
    Decode and validate JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        jwt.ExpiredSignatureError: If token is expired
        jwt.InvalidTokenError: If token is invalid
    """
    ...


def verify_token(token: str) -> bool:
    """Verify if token is valid."""
    ...
```

**Tasks:**

- [ ] Add type hints to all auth modules
- [ ] Add type hints to security modules
- [ ] Add type hints to middleware
- [ ] Run MyPy: `mypy hermes/auth/ hermes/security/ hermes/middleware/`

---

### PHASE 9: Add Type Hints to Database & Models

**Files:**
- `hermes/database/models.py`
- `hermes/database/connection.py`
- `hermes/database/*.py`

**Example:** SQLAlchemy models with type hints

```python
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hermes.database.base import Base


class Tenant(Base):
    """Tenant model for multi-tenancy."""

    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    users: Mapped[List["User"]] = relationship(back_populates="tenant")
    matters: Mapped[List["Matter"]] = relationship(back_populates="tenant")


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="users")
```

**Tasks:**

- [ ] Add type hints to all SQLAlchemy models using `Mapped[T]`
- [ ] Add type hints to database connection functions
- [ ] Add type hints to query builders
- [ ] Run MyPy: `mypy hermes/database/`

---

### PHASE 10: Add Type Hints to Utilities & Helpers

**Files:**
- `hermes/utils/*.py`
- Helper modules

**Example:** `hermes/utils/validators.py`

```python
from typing import Optional
import re
from email_validator import validate_email, EmailNotValidError


def validate_email_address(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False


def validate_phone_number(
    phone: str,
    country_code: str = "US"
) -> Optional[str]:
    """
    Validate and normalize phone number.

    Args:
        phone: Phone number to validate
        country_code: ISO country code

    Returns:
        Normalized phone number or None if invalid
    """
    ...


def sanitize_string(
    text: str,
    max_length: Optional[int] = None,
    allow_html: bool = False
) -> str:
    """
    Sanitize string input.

    Args:
        text: Text to sanitize
        max_length: Optional maximum length
        allow_html: Whether to allow HTML tags

    Returns:
        Sanitized string
    """
    ...
```

**Tasks:**

- [ ] Add type hints to all utility functions
- [ ] Add type hints to helper modules
- [ ] Run MyPy: `mypy hermes/utils/`

---

### PHASE 11: Add Type Hints to API Routes

**Files:**
- `hermes/api/v1/*.py`
- FastAPI route handlers

**Example:** FastAPI routes with type hints

```python
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from hermes.auth.dependencies import get_current_user
from hermes.types import MatterID, TenantID
from hermes.database.models import User, Matter
from hermes.services.matter_service import MatterService


router = APIRouter(prefix="/matters", tags=["matters"])


class MatterCreate(BaseModel):
    """Request model for creating a matter."""
    client_id: str
    matter_type: str
    jurisdiction: str
    description: str


class MatterResponse(BaseModel):
    """Response model for matter data."""
    id: str
    client_id: str
    matter_type: str
    jurisdiction: str
    description: str
    status: str
    created_at: str

    class Config:
        from_attributes = True


@router.post(
    "/",
    response_model=MatterResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_matter(
    matter_data: MatterCreate,
    current_user: User = Depends(get_current_user),
    matter_service: MatterService = Depends()
) -> Matter:
    """
    Create a new legal matter.

    Args:
        matter_data: Matter creation data
        current_user: Authenticated user
        matter_service: Matter service dependency

    Returns:
        Created matter

    Raises:
        HTTPException: If creation fails
    """
    try:
        matter = await matter_service.create_matter(
            tenant_id=current_user.tenant_id,
            matter_data=matter_data.dict()
        )
        return matter
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[MatterResponse])
async def get_matters(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    matter_service: MatterService = Depends()
) -> List[Matter]:
    """Get matters for current user's tenant."""
    matters = await matter_service.get_matters(
        tenant_id=current_user.tenant_id,
        status=status,
        limit=limit,
        offset=offset
    )
    return matters
```

**Tasks:**

- [ ] Add type hints to all API route handlers
- [ ] Ensure Pydantic models have proper types
- [ ] Add type hints to dependency functions
- [ ] Run MyPy: `mypy hermes/api/`

---

### PHASE 12: Add Type Hints to Test Files

**Files:**
- `tests/**/*.py`

**Note:** Tests can be less strict but should still have basic type hints

```python
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient


@pytest.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for API testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_create_matter(
    authenticated_client: AsyncClient,
    sample_matter_data: dict[str, str]
) -> None:
    """Test creating a matter."""
    response = await authenticated_client.post(
        "/api/v1/matters",
        json=sample_matter_data
    )

    assert response.status_code == 201
    data: dict[str, Any] = response.json()
    assert "id" in data
```

**Tasks:**

- [ ] Add basic type hints to test fixtures
- [ ] Add type hints to test functions (return type: `None`)
- [ ] Add type hints to test helpers
- [ ] Run MyPy on tests (with less strict config)

---

### PHASE 13: Fix MyPy Errors Iteratively

**Strategy:**
1. Run MyPy on one module at a time
2. Fix all errors in that module
3. Move to next module
4. Repeat until all modules pass

**Common MyPy errors and fixes:**

**Error:** "Function is missing a return type annotation"
```python
# FIX: Add return type
def my_function() -> str:
    return "value"
```

**Error:** "Missing type parameters for generic type"
```python
# WRONG
def get_items() -> list:
    ...

# CORRECT
def get_items() -> list[str]:
    ...
```

**Error:** "Incompatible return value type"
```python
# WRONG
def get_id() -> int:
    return "123"  # Type error!

# CORRECT
def get_id() -> int:
    return 123
```

**Error:** "Need type annotation for variable"
```python
# WRONG
items = []  # Type unknown

# CORRECT
items: list[str] = []
```

**Error:** "Argument has incompatible type"
```python
# WRONG
def process(value: int) -> None:
    ...

process("string")  # Type error!

# CORRECT
process(123)
```

**Tasks:**

- [ ] Fix MyPy errors in `hermes/voice_pipeline.py`
- [ ] Fix MyPy errors in `hermes/main.py`
- [ ] Fix MyPy errors in `hermes/services/`
- [ ] Fix MyPy errors in `hermes/integrations/`
- [ ] Fix MyPy errors in `hermes/reasoning/`
- [ ] Fix MyPy errors in `hermes/auth/`
- [ ] Fix MyPy errors in `hermes/database/`
- [ ] Fix MyPy errors in `hermes/api/`
- [ ] Fix remaining MyPy errors

**Track progress:**
```bash
# Run MyPy and count errors
mypy hermes/ | grep -c "error:"

# Target: 0 errors
```

---

### PHASE 14: Run Full MyPy Check

**Tasks:**

- [ ] Run MyPy on entire codebase:
  ```bash
  mypy hermes/ --strict
  ```

- [ ] Verify zero errors:
  ```bash
  mypy hermes/ --strict | grep "Success"
  ```

- [ ] Run MyPy on tests (less strict):
  ```bash
  mypy tests/
  ```

- [ ] Generate MyPy report:
  ```bash
  mypy hermes/ --html-report mypy-report/
  open mypy-report/index.html
  ```

- [ ] Document any intentional type ignores with comments:
  ```python
  result = some_untyped_library()  # type: ignore[no-untyped-call]
  ```

---

### PHASE 15: Configure CI/CD for Type Checking

**File:** `.github/workflows/type-checking.yml`

```yaml
name: Type Checking

on: [push, pull_request]

jobs:
  mypy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install mypy

      - name: Install type stubs
        run: |
          pip install types-redis types-requests types-pyyaml

      - name: Run MyPy (strict mode)
        run: |
          mypy hermes/ --strict --show-error-codes

      - name: Run MyPy on tests
        run: |
          mypy tests/ --show-error-codes
        continue-on-error: true  # Tests can be less strict

      - name: Generate MyPy report
        if: always()
        run: |
          mypy hermes/ --html-report mypy-report/ --strict

      - name: Upload MyPy report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: mypy-report
          path: mypy-report/
```

**File:** Update `.github/workflows/code-quality.yml`

Add MyPy step to existing code quality workflow:

```yaml
- name: Run MyPy
  run: mypy hermes/ --strict
```

**Tasks:**
- [ ] Create `.github/workflows/type-checking.yml`
- [ ] Update code quality workflow
- [ ] Make MyPy check required for PR merges
- [ ] Configure branch protection rules

---

### PHASE 16: Add Pre-commit Hook for Type Checking

**File:** `.pre-commit-config.yaml` (update existing)

```yaml
repos:
  # ... existing hooks ...

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies:
          - types-redis
          - types-requests
          - types-pyyaml
        args: [--strict, --show-error-codes]
        files: ^hermes/
```

**Tasks:**
- [ ] Update `.pre-commit-config.yaml`
- [ ] Install type stubs: `pip install types-redis types-requests types-pyyaml`
- [ ] Test pre-commit: `pre-commit run mypy --all-files`
- [ ] Ensure all developers have pre-commit installed

---

### PHASE 17: Documentation

**File:** `docs/type-hints-guide.md`

Create comprehensive type hints documentation:

```markdown
# Type Hints Guide for HERMES

## Overview

HERMES uses Python 3.11+ type hints throughout the codebase for improved code quality, IDE support, and bug prevention.

## Type Hint Standards

### Basic Types

```python
def process_name(name: str) -> str:
    return name.upper()

def calculate_total(amount: int, tax: float) -> float:
    return amount * (1 + tax)
```

### Optional Types

```python
from typing import Optional

def get_user(user_id: str) -> Optional[User]:
    # May return None
    return db.query(User).get(user_id)
```

### Collections

```python
from typing import List, Dict, Set, Tuple

def get_tags() -> List[str]:
    return ["tag1", "tag2"]

def get_metadata() -> Dict[str, Any]:
    return {"key": "value"}

def get_coordinates() -> Tuple[float, float]:
    return (37.7749, -122.4194)
```

### Custom Types

```python
from hermes.types import ClioContactDict, MatterID

def create_contact(data: ClioContactDict) -> MatterID:
    ...
```

## Running MyPy

```bash
# Check entire codebase
mypy hermes/ --strict

# Check specific file
mypy hermes/voice_pipeline.py

# Generate HTML report
mypy hermes/ --html-report mypy-report/
```

## Common Patterns

[... more examples ...]
```

**Tasks:**
- [ ] Create `docs/type-hints-guide.md`
- [ ] Update CLAUDE.md with type hint examples
- [ ] Add type hints section to contribution guide
- [ ] Create cheat sheet for common patterns

**File:** `README.md` (update)

Add type checking badge:

```markdown
[![Type Checked: MyPy](https://img.shields.io/badge/type_checked-mypy-blue.svg)](http://mypy-lang.org/)
```

**Tasks:**
- [ ] Add MyPy badge to README
- [ ] Document type checking in README
- [ ] Link to type hints guide

---

## 📊 Validation Checklist

- [ ] Audit script created and run
- [ ] MyPy configured for strict mode
- [ ] Custom types module created (`hermes/types.py`)
- [ ] 100% of functions have parameter type hints
- [ ] 100% of functions have return type hints
- [ ] All class attributes typed
- [ ] Complex types use TypedDict/Protocol
- [ ] MyPy passes with strict mode (zero errors)
- [ ] CI/CD enforces type checking
- [ ] Pre-commit hook configured
- [ ] Documentation complete
- [ ] Type hints badge added to README

---

## 🎯 Success Metrics

- **Type Hint Coverage:** 100% (1,112/1,112 functions)
- **MyPy Errors:** 0 (strict mode)
- **CI/CD:** MyPy check passes on all commits
- **Documentation:** Complete type hints guide published

---

## 💡 AI Coding Assistant Instructions

**Execution Strategy:**

1. **PHASE 1:** Run audit to identify all functions without type hints
2. **PHASE 2:** Configure MyPy strict mode
3. **PHASE 3:** Create custom types module
4. **PHASES 4-12:** Add type hints module by module (prioritized)
5. **PHASE 13:** Fix MyPy errors iteratively
6. **PHASE 14:** Verify zero MyPy errors
7. **PHASES 15-16:** Configure CI/CD and pre-commit
8. **PHASE 17:** Complete documentation

**Key Guidelines:**
- Work on one module at a time
- Run MyPy after each module to catch errors early
- Use custom types from `hermes/types.py`
- Prefer specific types over `Any`
- Document complex types with examples
- Add `# type: ignore` only as last resort (with explanation)

**Priority Order:**
1. Core modules (voice_pipeline, main, config)
2. Services
3. Integrations
4. AI/Reasoning
5. Auth & Security
6. Database
7. API routes
8. Utilities
9. Tests

---

## 📚 Reference Documentation

- [Python Typing Module](https://docs.python.org/3/library/typing.html)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
- [PEP 526 - Variable Annotations](https://peps.python.org/pep-0526/)
- [Real Python: Type Checking](https://realpython.com/python-type-checking/)

---

**Issue Priority:** 🟡 **MEDIUM**
**Estimated Complexity:** Medium
**Blocking:** Code Quality (not deployment)
**Dependencies:** None
**Milestone:** Production Readiness - Phase 3
