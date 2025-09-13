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
    email: str
    full_name: str
    password_hash: str
    roles: List[Role] = []
    is_active: bool = True
    created_at: str
    updated_at: str
    last_login_at: str | None = None


class UserCreate(BaseModel):
    """Data for creating a new user."""

    email: str
    full_name: str
    password_hash: str
    roles: List[Role] | None = None


class UserUpdate(BaseModel):
    """Data for updating a user."""

    email: str | None = None
    full_name: str | None = None
    password_hash: str | None = None
    roles: List[Role] | None = None
    is_active: bool | None = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
