"""Create authentication schema with RLS

Revision ID: 001_auth_schema
Revises: 
Create Date: 2024-12-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_auth_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create authentication schema with multi-tenant RLS."""
    
    # Create tenants table
    op.create_table('tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('tier', sa.String(50), nullable=False, default='standard'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create users table with tenant isolation
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('roles', postgresql.ARRAY(sa.String(50)), nullable=False, default=[]),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_tenant_email'),
        sa.Index('idx_users_email', 'email'),
        sa.Index('idx_users_tenant_id', 'tenant_id'),
    )
    
    # Create sessions table for token management
    op.create_table('user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('refresh_token_hash', sa.String(255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_used_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.Index('idx_sessions_user_id', 'user_id'),
        sa.Index('idx_sessions_tenant_id', 'tenant_id'),
        sa.Index('idx_sessions_expires_at', 'expires_at'),
    )
    
    # Create audit log table
    op.create_table('audit_logs',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('table_name', sa.String(50), nullable=False),
        sa.Column('operation', sa.String(10), nullable=False),
        sa.Column('old_data', postgresql.JSONB(), nullable=True),
        sa.Column('new_data', postgresql.JSONB(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.Index('idx_audit_tenant_timestamp', 'tenant_id', 'timestamp'),
        sa.Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        sa.Index('idx_audit_table_name', 'table_name'),
    )
    
    # Enable Row Level Security on all tables
    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY") 
    op.execute("ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY")
    
    # Create RLS policies for tenant isolation
    
    # Tenants: Users can only see their own tenant
    op.execute("""
        CREATE POLICY tenant_isolation_tenants ON tenants
        USING (id = current_setting('app.current_tenant', true)::uuid)
        WITH CHECK (id = current_setting('app.current_tenant', true)::uuid)
    """)
    
    # Users: Tenant isolation
    op.execute("""
        CREATE POLICY tenant_isolation_users ON users
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
        WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)
    
    # User sessions: Tenant isolation
    op.execute("""
        CREATE POLICY tenant_isolation_user_sessions ON user_sessions
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
        WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)
    
    # Audit logs: Tenant isolation
    op.execute("""
        CREATE POLICY tenant_isolation_audit_logs ON audit_logs
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
        WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)
    
    # Create function to automatically update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create triggers for updated_at
    op.execute("""
        CREATE TRIGGER update_tenants_updated_at
        BEFORE UPDATE ON tenants
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Create indexes for performance
    op.create_index('idx_users_full_name', 'users', ['full_name'])
    op.create_index('idx_users_roles', 'users', ['roles'], postgresql_using='gin')
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    op.create_index('idx_users_last_login', 'users', ['last_login_at'])
    
    # Create function for generating UUIDs if not exists
    op.execute("""
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    """)


def downgrade():
    """Drop authentication schema."""
    
    # Drop triggers first
    op.execute("DROP TRIGGER IF EXISTS update_users_updated_at ON users")
    op.execute("DROP TRIGGER IF EXISTS update_tenants_updated_at ON tenants")
    
    # Drop function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop indexes
    op.drop_index('idx_users_last_login')
    op.drop_index('idx_users_created_at')
    op.drop_index('idx_users_roles')
    op.drop_index('idx_users_full_name')
    
    # Drop tables (CASCADE will handle RLS policies)
    op.drop_table('audit_logs')
    op.drop_table('user_sessions')
    op.drop_table('users')
    op.drop_table('tenants')
    
    # Drop extension
    op.execute("DROP EXTENSION IF EXISTS \"uuid-ossp\"")