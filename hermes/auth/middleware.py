"""FastAPI middleware enforcing JWT authentication and tenant isolation."""
from __future__ import annotations
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

from .jwt_handler import JWTHandler
from .models import TokenPayload
from ..config import settings
from ..database.tenant_context import tenant_context


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
        token = auth_header.split()[1]
        try:
            payload: TokenPayload = self.jwt_handler.decode(token)
        except Exception:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        # set tenant context
        token_tenant = payload.tenant_id
        request.state.tenant_id = token_tenant
        token_var = tenant_context.set(token_tenant)
        try:
            response = await call_next(request)
        finally:
            tenant_context.reset(token_var)
        return response
