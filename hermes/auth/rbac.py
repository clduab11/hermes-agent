"""Role-based access control utilities."""
from __future__ import annotations

from typing import Iterable, Sequence

from fastapi import Depends, HTTPException, Request, status

from .models import Role


def has_role(user_roles: Iterable[Role], required: Sequence[Role]) -> bool:
    """Return True if any of the required roles is present."""
    return any(role in set(user_roles) for role in required)


def require_roles(*required: Role):
    """FastAPI dependency to enforce role membership."""

    async def _dependency(request: Request) -> None:
        roles = getattr(request.state, "roles", [])
        if not has_role(roles, required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

    return Depends(_dependency)
