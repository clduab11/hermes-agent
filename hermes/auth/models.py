"""Domain models for authentication and tenant management."""

from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel


class Tenant(BaseModel):
    """Represents an organisation/tenant within the system."""

    id: str
    name: str
    tier: str


class Role(str, Enum):
    """Available user roles."""

    ADMIN = "admin"
    ATTORNEY = "attorney"
    STAFF = "staff"
    READ_ONLY = "read-only"


class TokenPayload(BaseModel):
    """JWT payload extracted after token validation."""

    sub: str
    tenant_id: str
    exp: int
    type: str
    roles: List[Role] = []


class User(BaseModel):
    """Application user with tenant scoped roles."""

    id: str
    tenant_id: str
    roles: List[Role] = []


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
