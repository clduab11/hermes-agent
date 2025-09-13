"""Security middleware for OWASP compliance and protection."""

from __future__ import annotations

import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that adds security headers for OWASP compliance."""

    def __init__(self, app, enable_hsts: bool = True, enable_csp: bool = True) -> None:
        super().__init__(app)
        self.enable_hsts = enable_hsts
        self.enable_csp = enable_csp

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        response = await call_next(request)

        # HSTS (HTTP Strict Transport Security)
        if self.enable_hsts and request.url.scheme == "https":
            response.headers[
                "Strict-Transport-Security"
            ] = "max-age=31536000; includeSubDomains"

        # Content Security Policy
        if self.enable_csp:
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' wss: ws:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
            response.headers["Content-Security-Policy"] = csp_policy

        # Additional security headers
        response.headers.update(
            {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Permissions-Policy": (
                    "geolocation=(), microphone=(), camera=(), "
                    "payment=(), usb=(), accelerometer=(), gyroscope=()"
                ),
            }
        )

        # Remove server header for security through obscurity
        response.headers.pop("Server", None)

        return response
