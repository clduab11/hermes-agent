# Supabase Database Setup Guide

This guide walks you through setting up Supabase as the primary database for HERMES.

---

## Overview

HERMES uses Supabase (managed PostgreSQL) for:
- User authentication and authorization
- API key management
- Conversation logs and audit trails
- Matter data and client information
- Usage metrics and billing data

**Why Supabase?**
- Managed PostgreSQL 15+ with automatic backups
- Row-Level Security (RLS) for multi-tenancy
- Real-time subscriptions support
- RESTful API auto-generated from schema
- Easy migration from other PostgreSQL databases

---

## Step 1: Create Supabase Account

1. Go to [supabase.com](https://supabase.com/)
2. Click "Start your project" or "Sign Up"
3. Sign up with GitHub, Google, or email
4. Verify your email address

---

## Step 2: Create New Project

1. Click "New Project" in your organization
2. Fill in project details:
   - **Name**: `HERMES Legal AI` (or your preferred name)
   - **Database Password**: Generate strong password (save securely!)
   - **Region**: Choose region close to your GCP deployment
     - US: `us-east-1` or `us-west-1`
     - Europe: `eu-west-1`
     - Asia: `ap-southeast-1`
   - **Pricing Plan**: 
     - Free (for development)
     - Pro ($25/month - recommended for production)
3. Click "Create new project"
4. Wait 2-3 minutes for project provisioning

---

## Step 3: Enable Row-Level Security (RLS)

RLS is critical for multi-tenant isolation and security.

### Via Supabase Dashboard

1. Go to **Database** → **Tables**
2. For each table created by migrations:
   - Click table name
   - Go to **Policies** tab
   - Toggle "Enable RLS" to ON

### Via SQL

```sql
-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE matters ENABLE ROW LEVEL SECURITY;
```

---

## Step 4: Get Database Credentials

### Connection String

1. Go to **Settings** → **Database**
2. Scroll to **Connection string**
3. Select **URI** tab
4. Copy the connection string
5. Replace `[YOUR-PASSWORD]` with your database password
6. Save as `DATABASE_URL` in your `.env` file

**Format**:
```
postgresql://postgres:[YOUR-PASSWORD]@db.[project-ref].supabase.co:5432/postgres
```

### Supabase URL

1. Go to **Settings** → **API**
2. Copy **URL** under "Project URL"
3. Save as `SUPABASE_URL` in your `.env` file

**Format**:
```
https://[project-ref].supabase.co
```

### Service Role Key

1. Go to **Settings** → **API**
2. Under "Project API keys", copy **service_role** key
3. Save as `SUPABASE_SERVICE_ROLE_KEY` in your `.env` file

⚠️ **Security Warning**: 
- Service role key bypasses RLS and has full database access
- NEVER expose this key to client-side code
- Only use server-side (backend)
- Store in GCP Secret Manager for production

**Format**:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Step 5: Run Database Migrations

HERMES uses Alembic for database migrations.

### Verify Configuration

Check `alembic.ini`:
```ini
sqlalchemy.url = postgresql://postgres:password@localhost:5432/hermes
```

This will be overridden by the `DATABASE_URL` environment variable.

### Apply Migrations

```bash
# Ensure .env is configured with DATABASE_URL
source .env  # or use your virtual environment

# Run all migrations to latest
alembic upgrade head

# Verify migrations applied
alembic current
```

### Expected Output

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade -> 001_initial_schema
INFO  [alembic.runtime.migration] Running upgrade 001_initial_schema -> 002_add_rls_policies
INFO  [alembic.runtime.migration] Running upgrade 002_add_rls_policies -> head
```

### View Migration History

```bash
# View all migrations
alembic history

# View current version
alembic current
```

---

## Step 6: Verify Database Schema

### Via Supabase Dashboard

1. Go to **Database** → **Tables**
2. Verify these tables exist:
   - `users` - User accounts
   - `api_keys` - API key management
   - `usage_logs` - Usage tracking
   - `conversations` - Conversation history
   - `matters` - Legal matters/cases
   - `alembic_version` - Migration tracking

### Via SQL Editor

1. Go to **SQL Editor**
2. Run this query:

```sql
-- List all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- Count records in each table
SELECT 
  'users' as table, COUNT(*) as records FROM users
UNION ALL
SELECT 'api_keys', COUNT(*) FROM api_keys
UNION ALL
SELECT 'usage_logs', COUNT(*) FROM usage_logs
UNION ALL
SELECT 'conversations', COUNT(*) FROM conversations
UNION ALL
SELECT 'matters', COUNT(*) FROM matters;
```

---

## Step 7: Configure RLS Policies

RLS policies ensure users can only access their own data.

### Example Policies

```sql
-- Users can only read their own profile
CREATE POLICY "Users can view own profile"
  ON users FOR SELECT
  USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
  ON users FOR UPDATE
  USING (auth.uid() = id);

-- API keys are visible only to the owner
CREATE POLICY "Users can view own API keys"
  ON api_keys FOR SELECT
  USING (auth.uid() = user_id);

-- Conversations are only accessible to the user
CREATE POLICY "Users can view own conversations"
  ON conversations FOR SELECT
  USING (auth.uid() = user_id);
```

**Note**: Full RLS policies should be defined in Alembic migrations.

---

## Step 8: Test Database Connection

### Using psql

```bash
# Install psql (if not already installed)
# Ubuntu/Debian: sudo apt-get install postgresql-client
# Mac: brew install postgresql
# Windows: Download from postgresql.org

# Test connection
psql "postgresql://postgres:[PASSWORD]@db.[project-ref].supabase.co:5432/postgres"

# Should see:
# psql (15.x)
# SSL connection (protocol: TLSv1.3, cipher: TLS_AES_256_GCM_SHA384)
# Type "help" for help.
# postgres=>
```

### Using Python

```python
import asyncpg
import asyncio

async def test_connection():
    conn = await asyncpg.connect("postgresql://postgres:[PASSWORD]@db.[project-ref].supabase.co:5432/postgres")
    version = await conn.fetchval('SELECT version()')
    print(f"Connected! PostgreSQL version: {version}")
    await conn.close()

asyncio.run(test_connection())
```

---

## Step 9: Configure Connection Pooling

For production, connection pooling is essential.

### Supabase Built-in Pooling

Supabase provides connection pooling via PgBouncer.

**Connection String for Pooling**:
```
postgresql://postgres:[PASSWORD]@db.[project-ref].supabase.co:6543/postgres?pgbouncer=true
```

**Key Differences**:
- Port: `6543` (instead of `5432`)
- Add `?pgbouncer=true` parameter
- Transaction mode (not session mode)

### Configure in HERMES

Update `.env`:
```bash
# Use pooled connection for production
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[project-ref].supabase.co:6543/postgres?pgbouncer=true
```

**Pool Limits** (Pro Plan):
- Max connections: 120 (can be increased)
- Idle timeout: 600 seconds
- Max client connections: 1000

---

## Troubleshooting

### Issue: Connection Timeout

**Error**: `asyncpg.exceptions.ConnectionTimeoutError`

**Solutions**:
- Check Supabase project is not paused (Free tier pauses after inactivity)
- Verify internet connection
- Check firewall isn't blocking port 5432
- Ensure password is correct (no special character encoding issues)

### Issue: SSL/TLS Error

**Error**: `SSL SYSCALL error: Connection reset by peer`

**Solutions**:
- Add `?sslmode=require` to connection string
- Update PostgreSQL client libraries
- Try connection pooler port (6543) instead of direct (5432)

### Issue: Authentication Failed

**Error**: `password authentication failed for user "postgres"`

**Solutions**:
- Double-check password (no extra spaces/characters)
- Reset database password in Supabase dashboard
- Use URL-encoded password if it contains special characters

### Issue: Too Many Connections

**Error**: `remaining connection slots are reserved`

**Solutions**:
- Use connection pooling (port 6543)
- Upgrade to Pro plan (more connections)
- Close unused connections in code
- Configure SQLAlchemy connection pool properly

### Issue: Row-Level Security Blocking Queries

**Error**: `new row violates row-level security policy`

**Solutions**:
- Use service role key for admin operations
- Ensure RLS policies allow the operation
- Check `auth.uid()` is set correctly
- Temporarily disable RLS for debugging (not production)

---

## Performance Optimization

### Indexing

Critical indexes for HERMES:

```sql
-- User lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);

-- API key lookups
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);

-- Usage logs (for billing)
CREATE INDEX idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX idx_usage_logs_created_at ON usage_logs(created_at);
CREATE INDEX idx_usage_logs_user_created ON usage_logs(user_id, created_at);

-- Conversations (for retrieval)
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
```

### Query Optimization

Use `EXPLAIN ANALYZE` to identify slow queries:

```sql
EXPLAIN ANALYZE 
SELECT * FROM usage_logs 
WHERE user_id = 'xxx' 
AND created_at > NOW() - INTERVAL '30 days';
```

### Caching

Use Redis for frequently accessed data:
- User profiles
- API key validation
- Usage counts (for rate limiting)

---

## Backups & Disaster Recovery

### Automatic Backups (Pro Plan)

- **Daily backups**: 7 days retention
- **Weekly backups**: 4 weeks retention
- **Point-in-time recovery**: Up to 7 days

### Manual Backups

```bash
# Dump entire database
pg_dump "postgresql://postgres:[PASSWORD]@db.[project-ref].supabase.co:5432/postgres" > backup.sql

# Restore from backup
psql "postgresql://postgres:[PASSWORD]@db.[project-ref].supabase.co:5432/postgres" < backup.sql
```

### Database Migration

To migrate to a new Supabase project:

```bash
# Dump from old project
pg_dump "OLD_DATABASE_URL" > migration.sql

# Restore to new project
psql "NEW_DATABASE_URL" < migration.sql

# Run migrations to update schema
alembic upgrade head
```

---

## Monitoring

### Via Supabase Dashboard

1. Go to **Reports**
2. Monitor:
   - Database size
   - Connection count
   - Query performance
   - API requests

### Via SQL Queries

```sql
-- Database size
SELECT pg_size_pretty(pg_database_size(current_database()));

-- Table sizes
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Active connections
SELECT count(*) FROM pg_stat_activity;
```

---

## Cost Considerations

### Free Plan
- **Database Size**: 500 MB
- **Bandwidth**: 2 GB/month
- **API Requests**: Unlimited
- **Cost**: $0/month
- **Pausing**: Auto-pauses after 1 week inactivity

### Pro Plan
- **Database Size**: 8 GB (+ $0.125/GB overage)
- **Bandwidth**: 50 GB/month (+ $0.09/GB overage)
- **API Requests**: Unlimited
- **Cost**: $25/month
- **Pausing**: Never pauses

### Enterprise Plan
- **Custom limits**
- **Dedicated resources**
- **SLA guarantees**
- **Contact for pricing**

**Recommendation**: 
- **Development**: Free plan
- **Production**: Pro plan minimum
- **High-scale**: Enterprise plan

---

## Next Steps

Once Supabase is configured:

1. ✅ Test connection with `psql` or Python
2. ✅ Verify all tables created
3. ✅ Configure `.env` with credentials
4. ✅ Set up other services (OpenAI, Stripe, etc.)
5. ✅ Continue with deployment: [DEPLOYMENT.md](../../DEPLOYMENT.md)

---

## Support

- **Supabase Docs**: [supabase.com/docs](https://supabase.com/docs)
- **Supabase Support**: [supabase.com/support](https://supabase.com/support)
- **Community**: [Discord](https://discord.supabase.com/)
- **HERMES Support**: info@parallax-ai.app

---

**Last Updated**: 2024-11-19
