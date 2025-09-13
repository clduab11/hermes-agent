"""Add clio_tokens table for OAuth storage

Revision ID: 002_clio_tokens
Revises: 001_auth_schema
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_clio_tokens'
down_revision = '001_auth_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Create clio_tokens table with RLS and policies."""
    op.create_table(
        'clio_tokens',
        sa.Column('tenant_id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('token_type', sa.String(20), nullable=False, server_default='Bearer'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('tenant_id', 'user_id', name='pk_clio_tokens')
    )

    # Enable RLS and add tenant isolation policy
    op.execute("ALTER TABLE clio_tokens ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation_clio_tokens ON clio_tokens
        USING (tenant_id = current_setting('app.current_tenant', true))
        WITH CHECK (tenant_id = current_setting('app.current_tenant', true))
    """)


def downgrade():
    op.drop_table('clio_tokens')
