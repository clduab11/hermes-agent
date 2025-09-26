-- HERMES AI Voice Agent System - PostgreSQL Initialization Script
-- Production-ready database setup for enterprise law firm deployments

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "hstore";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create additional database for testing if in development mode
DO $$
BEGIN
    IF current_setting('server_version_num')::int >= 110000 THEN
        -- PostgreSQL 11+ supports IF NOT EXISTS for databases
        PERFORM 1;
    END IF;
EXCEPTION
    WHEN others THEN
        NULL; -- Ignore errors for production deployments
END $$;

-- Set timezone to UTC for consistent timestamp handling
SET timezone = 'UTC';

-- Create performance optimization settings
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET pg_stat_statements.track = 'all';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET log_min_duration_statement = 1000;
ALTER SYSTEM SET log_checkpoints = on;
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_lock_waits = on;
ALTER SYSTEM SET log_temp_files = 0;
ALTER SYSTEM SET log_autovacuum_min_duration = 0;

-- Create indexes for common queries (these will be managed by Alembic in production)
-- This is just for reference and initial optimization

-- Session and user management indexes
-- CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
-- CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
-- CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
-- CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);

-- Voice processing indexes
-- CREATE INDEX IF NOT EXISTS idx_voice_sessions_user_id ON voice_sessions(user_id);
-- CREATE INDEX IF NOT EXISTS idx_voice_sessions_created_at ON voice_sessions(created_at);
-- CREATE INDEX IF NOT EXISTS idx_transcriptions_session_id ON transcriptions(session_id);

-- Knowledge graph indexes
-- CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_type ON knowledge_nodes(node_type);
-- CREATE INDEX IF NOT EXISTS idx_knowledge_edges_source ON knowledge_edges(source_node_id);
-- CREATE INDEX IF NOT EXISTS idx_knowledge_edges_target ON knowledge_edges(target_node_id);

-- Audit logging indexes
-- CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
-- CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
-- CREATE INDEX IF NOT EXISTS idx_audit_logs_action_type ON audit_logs(action_type);

-- Full-text search indexes
-- CREATE INDEX IF NOT EXISTS idx_conversations_fts ON conversations USING gin(to_tsvector('english', content));
-- CREATE INDEX IF NOT EXISTS idx_legal_documents_fts ON legal_documents USING gin(to_tsvector('english', document_text));

-- Performance monitoring table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC NOT NULL,
    metric_unit VARCHAR(20),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    tenant_id VARCHAR(50),
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_performance_metrics_name_timestamp
ON performance_metrics(metric_name, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_performance_metrics_tenant_timestamp
ON performance_metrics(tenant_id, timestamp DESC);

-- Maintenance functions
CREATE OR REPLACE FUNCTION cleanup_old_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete sessions older than 30 days
    DELETE FROM sessions WHERE created_at < NOW() - INTERVAL '30 days';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    -- Log the cleanup
    INSERT INTO performance_metrics (metric_name, metric_value, metric_unit, metadata)
    VALUES ('sessions_cleaned', deleted_count, 'count',
            jsonb_build_object('cleanup_date', CURRENT_TIMESTAMP));

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete audit logs older than 1 year (compliance requirement)
    DELETE FROM audit_logs WHERE timestamp < NOW() - INTERVAL '1 year';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    -- Log the cleanup
    INSERT INTO performance_metrics (metric_name, metric_value, metric_unit, metadata)
    VALUES ('audit_logs_cleaned', deleted_count, 'count',
            jsonb_build_object('cleanup_date', CURRENT_TIMESTAMP));

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Database health check function
CREATE OR REPLACE FUNCTION database_health_check()
RETURNS JSON AS $$
DECLARE
    result JSON;
    connection_count INTEGER;
    active_queries INTEGER;
    database_size BIGINT;
BEGIN
    -- Get connection count
    SELECT COUNT(*) INTO connection_count
    FROM pg_stat_activity
    WHERE state = 'active';

    -- Get active query count
    SELECT COUNT(*) INTO active_queries
    FROM pg_stat_activity
    WHERE state = 'active' AND query != '<IDLE>';

    -- Get database size
    SELECT pg_database_size(current_database()) INTO database_size;

    -- Build result
    result := json_build_object(
        'status', 'healthy',
        'connection_count', connection_count,
        'active_queries', active_queries,
        'database_size_bytes', database_size,
        'database_size_mb', ROUND(database_size / (1024.0 * 1024.0), 2),
        'timestamp', CURRENT_TIMESTAMP
    );

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Create a simple monitoring view
CREATE OR REPLACE VIEW system_health AS
SELECT
    'database' as component,
    database_health_check() as metrics,
    CURRENT_TIMESTAMP as last_check;

-- Grant necessary permissions to the hermes user
-- (Alembic will handle most permissions, but these are essential)
GRANT USAGE ON SCHEMA public TO hermes;
GRANT CREATE ON SCHEMA public TO hermes;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO hermes;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO hermes;

-- Set default permissions for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO hermes;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO hermes;

-- Log successful initialization
INSERT INTO performance_metrics (metric_name, metric_value, metric_unit, metadata)
VALUES ('database_initialized', 1, 'boolean',
        jsonb_build_object(
            'initialization_date', CURRENT_TIMESTAMP,
            'version', version(),
            'timezone', current_setting('timezone')
        ));

-- Create a welcome message for the logs
DO $$
BEGIN
    RAISE NOTICE 'HERMES AI Voice Agent System database initialized successfully';
    RAISE NOTICE 'Database: %, User: %, Timezone: %',
        current_database(), current_user, current_setting('timezone');
END $$;