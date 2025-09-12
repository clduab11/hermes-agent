"""Tenant context utilities."""
from contextvars import ContextVar
from typing import Optional
from dataclasses import dataclass


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
tenant_context: ContextVar[TenantContext | None] = ContextVar("tenant_context", default=None)


def get_current_tenant() -> str | None:
    """Return the tenant ID for the current request."""
    context = tenant_context.get()
    return context.tenant_id if context else None


def get_tenant_context() -> TenantContext:
    """Get the current tenant context or create a default one."""
    context = tenant_context.get()
    if context is None:
        # Return default context for demo/testing
        return TenantContext(tenant_id="default", user_id="demo_user", permissions=["*"])
    return context


def set_tenant_context(context: TenantContext):
    """Set the tenant context for the current request."""
    tenant_context.set(context)
