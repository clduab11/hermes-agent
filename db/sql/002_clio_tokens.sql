-- Create clio_tokens table for OAuth storage (no Alembic required)
-- Fields are TEXT to avoid strict UUID coupling with JWT subject values

CREATE TABLE IF NOT EXISTS clio_tokens (
  tenant_id     VARCHAR(100) NOT NULL,
  user_id       VARCHAR(100) NOT NULL,
  access_token  TEXT NOT NULL,
  refresh_token TEXT NOT NULL,
  expires_at    TIMESTAMPTZ NOT NULL,
  token_type    VARCHAR(20) NOT NULL DEFAULT 'Bearer',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT pk_clio_tokens PRIMARY KEY (tenant_id, user_id)
);

-- Enable Row Level Security
ALTER TABLE clio_tokens ENABLE ROW LEVEL SECURITY;

-- Tenant isolation policy using app.current_tenant setting
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' AND tablename = 'clio_tokens' AND policyname = 'tenant_isolation_clio_tokens'
  ) THEN
    CREATE POLICY tenant_isolation_clio_tokens ON clio_tokens
    USING (tenant_id = current_setting('app.current_tenant', true))
    WITH CHECK (tenant_id = current_setting('app.current_tenant', true));
  END IF;
END $$;

