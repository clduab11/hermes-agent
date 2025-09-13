"""FastAPI middleware enforcing JWT authentication and tenant isolation.

Also provides lightweight dependencies for `get_current_user` and
`require_permission` to support API modules without a full user DB.
"""
from __future__ import annotations
from typing import Callable, Optional

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from .jwt_handler import JWTHandler
from .models import TokenPayload, Role
from ..database.tenant_context import tenant_context, TenantContext


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Middleware that validates JWTs and sets tenant context."""

    def __init__(self, app, jwt_handler: JWTHandler | None = None) -> None:
        super().__init__(app)
        self.jwt_handler = jwt_handler or JWTHandler()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        if request.url.path.startswith("/health") or request.url.path.startswith("/auth/"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing credentials"})
        try:
            token = auth_header.split()[1]
        except IndexError:
            return JSONResponse(status_code=401, content={"detail": "Missing token"})
        try:
            payload: TokenPayload = self.jwt_handler.decode(token)
            if payload.type != "access":
                raise ValueError("Wrong token type")
        except Exception:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        # set tenant context and request state
        token_tenant = payload.tenant_id
        request.state.tenant_id = token_tenant
        request.state.user_id = payload.sub
        request.state.roles = payload.roles
        # Store full tenant context for downstream dependencies
        token_var = tenant_context.set(
            TenantContext(tenant_id=token_tenant, user_id=payload.sub, permissions=[])
        )
        try:
            response = await call_next(request)
        finally:
            tenant_context.reset(token_var)
        return response


# Lightweight dependencies expected by some API routers
async def get_current_user(request: Request) -> dict:
    """Return a minimal current-user object from request state.

    This avoids a hard dependency on a database-backed user repository.
    """
    user_id: Optional[str] = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # Best-effort email inference for display purposes
    email = user_id if "@" in user_id else f"{user_id}@local"
    return {
        "id": user_id,
        "email": email,
        "tenant_id": getattr(request.state, "tenant_id", None),
        "roles": [r.value if isinstance(r, Role) else r for r in getattr(request.state, "roles", [])],
    }


def require_permission(permission: str):
    """FastAPI-style dependency to enforce a simple permission mapping.

    Mapping defaults to ADMIN for unknown permissions. Known examples:
    - analytics:read -> [admin, attorney, staff]
    - billing:manage -> [admin]
    - clio:read -> [admin, attorney, staff]
    - clio:write -> [admin, attorney]
    """

    allowed_by_permission = {
        "analytics:read": {Role.ADMIN, Role.ATTORNEY, Role.STAFF},
        "billing:manage": {Role.ADMIN},
        "clio:read": {Role.ADMIN, Role.ATTORNEY, Role.STAFF},
        "clio:write": {Role.ADMIN, Role.ATTORNEY},
    }

    required_roles = allowed_by_permission.get(permission, {Role.ADMIN})

    async def _dependency(request: Request) -> None:
        roles = set(getattr(request.state, "roles", []) or [])
        # Normalize to Role enum if roles are strings
        normalized: set[Role] = set()
        for r in roles:
            if isinstance(r, Role):
                normalized.add(r)
            else:
                try:
                    normalized.add(Role(r))
                except Exception:
                    continue
        if normalized.isdisjoint(required_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    return _dependency
