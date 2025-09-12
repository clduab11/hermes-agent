# Authentication & Multi-Tenant Isolation Layer

This document describes the authentication and tenant isolation architecture introduced in PR #001. It provides an overview of the core components, setup steps, and testing commands.

## Architecture Overview
- **JWT authentication** implemented in `hermes/auth/jwt_handler.py` using RS256 signing with 15‑minute access tokens and 7‑day refresh tokens.
- **Tenant isolation middleware** in `hermes/auth/middleware.py` ensures every request is scoped to a tenant and automatically rewrites database queries.
- **Database context** layer (`hermes/database/tenant_context.py`) applies tenant filters and row‑level security policies defined in migration `001_add_tenant_isolation.sql`.
- **WebSocket authentication** handled by `hermes/websocket_handler.py` validates tokens on connection and disconnects when tokens expire.

## Environment Variables
- `JWT_PRIVATE_KEY` – RSA private key for signing tokens
- `JWT_PUBLIC_KEY` – RSA public key for validation
- `JWT_ALGORITHM` – defaults to `RS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES` – default `15`
- `REFRESH_TOKEN_EXPIRE_DAYS` – default `7`

## Migration Steps
1. Generate RSA key pair:
   ```bash
   openssl genrsa -out private_key.pem 2048
   openssl rsa -in private_key.pem -pubout -out public_key.pem
   ```
2. Run database migrations:
   ```bash
   alembic upgrade head
   ```
3. Create a tenant for testing:
   ```bash
   python -m hermes.auth.create_tenant --name "Demo Law Firm" --tier "professional"
   ```
4. Generate API keys for existing integrations:
   ```bash
   python -m hermes.auth.generate_keys --tenant-id <uuid>
   ```

## API Usage
1. **Obtain a token**
   ```bash
   curl -X POST http://localhost:8000/auth/token \
     -H "Content-Type: application/json" \
     -d '{"client_id": "test", "client_secret": "secret"}'
   ```
2. **Call a protected endpoint**
   ```bash
   curl http://localhost:8000/api/voice/status \
     -H "Authorization: Bearer <token>"
   ```
3. **WebSocket connection**
   ```bash
   wscat -c "ws://localhost:8000/ws?token=<token>"
   ```

## Acceptance Criteria
- Endpoints reject requests without a valid token.
- Tenant A cannot access Tenant B’s data.
- WebSocket connections close when tokens expire.
- Token refresh works without re‑authentication.
- Audit logs capture all authentication events.
- Performance regression remains under 5 ms p99.
- `bandit` security scan reports zero vulnerabilities.

## Testing
Run the auth test suite:
```bash
pytest tests/auth/ -v --cov=hermes.auth --cov-report=term-missing
```

## Next Steps
- Implement role-based access control.
- Track per‑tenant usage for billing.
- Provide tenant‑specific analytics dashboards.
