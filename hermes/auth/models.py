"""Domain models for authentication and tenant management."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Tenant(BaseModel):
    id: str
    name: str
    tier: str


class TokenPayload(BaseModel):
    sub: str
    tenant_id: str
    exp: int
    type: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
