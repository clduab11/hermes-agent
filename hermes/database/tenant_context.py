"""Tenant context utilities."""

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, status


@dataclass
class TenantContext:
    """Container for tenant context information."""

    tenant_id: str
    user_id: Optional[str] = None
    permissions: list[str] = None

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []


# Context variable storing current tenant context
tenant_context: ContextVar[TenantContext | None] = ContextVar(
    "tenant_context", default=None
)


def get_current_tenant() -> str | None:
    """Return the tenant ID for the current request."""
    context = tenant_context.get()
    return context.tenant_id if context else None


def get_tenant_context() -> TenantContext:
    """Get the current tenant context or raise if unauthenticated."""
    context = tenant_context.get()
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Tenant context required"
        )
    if isinstance(context, TenantContext):
        return context
    # Backward compatibility: handle legacy string value
    return TenantContext(tenant_id=str(context), user_id=None, permissions=[])


def set_tenant_context(context: TenantContext):
    """Set the tenant context for the current request."""
    tenant_context.set(context)
