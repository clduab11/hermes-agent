Supabase Setup for Hermes
=========================

Goal
- Connect Hermes to your Supabase project for Postgres, RLS, and MCP integration.

What You Need
- Supabase Project URL (e.g., https://YOUR-PROJECT.supabase.co)
- Supabase anon public key (browser/limited use; Hermes doesn’t use this by default)
- Supabase service_role key (server-side only; keep secret)
- Postgres connection details (Supabase provides a connection string)

Environment Variables
- Set these in your Hermes runtime (do not commit to git):

  export SUPABASE_URL="https://YOUR-PROJECT.supabase.co"
  export SUPABASE_ANON_KEY="<anon key>"
  export SUPABASE_SERVICE_ROLE_KEY="<service role key>"

  # Postgres connection used by Hermes async SQLAlchemy engine
  # Note: Use asyncpg driver and URL-encode passwords with special characters
  export DATABASE_URL="postgresql+asyncpg://USER:PASSWORD@HOST:PORT/postgres"

  # Example (URL-encode special characters):
  #   PLAIN:   postgresql://postgres:[Pass&word]@db.PROJECT.supabase.co:5432/postgres
  #   ENCODED: postgresql+asyncpg://postgres:%5BPass%26word%5D@db.PROJECT.supabase.co:5432/postgres

How Hermes Uses Supabase
- Database (SQLAlchemy): Hermes connects directly to Supabase Postgres via `DATABASE_URL`.
  - The engine is async; Hermes auto-normalizes `postgresql://` → `postgresql+asyncpg://` if needed.
  - If `DATABASE_URL` is unset, analytics fall back to disabled/non-mock mode in production.
- MCP Orchestrator: Registers a Supabase MCP server if `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set.

Row Level Security (RLS)
- The repo includes an Alembic migration (`alembic/versions/001_auth_schema.py`) that sets up multi-tenant tables and RLS policies.
- Recommended approach:
  1) Generate an Alembic config or apply equivalent SQL via psql.
  2) Ensure the following before applying policies:
     - `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`
     - App role permissions per your security model.
- If you prefer SQL-only, port the CREATE TABLE and POLICY statements from the Alembic script to a SQL file and run via psql.

CORS and Networking
- Set Hermes `CORS_ALLOW_ORIGINS` to your web origins.
- Supabase Postgres is internet-accessible; ensure outbound egress from Hermes to the Supabase DB host/port 5432 is permitted.

Verification Steps
1) Set env vars and start Hermes (prod mode): DEBUG=false DEMO_MODE=false
2) Watch logs for: "Database connection initialized".
3) Hit `/health` and `/status`; analytics will show operational once DB-backed data exists.

Security Notes
- Never expose the service_role key to client-side code.
- Store keys in a secret manager in production and rotate periodically.
- Apply RLS and tenant context via the middleware to prevent cross-tenant access.

Troubleshooting
- Error about driver/dialect:
  - Ensure the URL begins with `postgresql+asyncpg://`.
- Auth errors to Supabase PostgREST/MCP:
  - Verify `SUPABASE_SERVICE_ROLE_KEY` is set; this is required for server-side operations.
