"""Tenant context utilities."""
from contextvars import ContextVar

# Context variable storing current tenant ID
tenant_context: ContextVar[str | None] = ContextVar("tenant_context", default=None)


def get_current_tenant() -> str | None:
    """Return the tenant ID for the current request."""
    return tenant_context.get()
