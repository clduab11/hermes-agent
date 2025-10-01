"""Add marketing tables

Revision ID: 003_marketing_tables
Revises: 002_clio_tokens
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_marketing_tables'
down_revision = '002_clio_tokens'
branch_labels = None
depends_on = None


def upgrade():
    """Create marketing tables for leads, social posts, and webhook events."""
    
    # Create leads table
    op.create_table(
        'leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('firm_name', sa.String(length=255), nullable=False),
        sa.Column('contact_name', sa.String(length=255), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('status', sa.Enum('new', 'contacted', 'qualified', 'demo_scheduled', 'proposal_sent', 'negotiating', 'won', 'lost', name='leadstatus'), nullable=False),
        sa.Column('firm_size', sa.String(length=50), nullable=True),
        sa.Column('practice_areas', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('jurisdiction', sa.String(length=100), nullable=True),
        sa.Column('pipeline_value', sa.Integer(), nullable=True),
        sa.Column('probability', sa.Integer(), nullable=True),
        sa.Column('expected_close_date', sa.DateTime(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('campaign', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_contacted', sa.DateTime(), nullable=True),
        sa.Column('tenant_id', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leads_firm_name'), 'leads', ['firm_name'], unique=False)
    op.create_index(op.f('ix_leads_contact_email'), 'leads', ['contact_email'], unique=False)
    op.create_index(op.f('ix_leads_status'), 'leads', ['status'], unique=False)
    op.create_index(op.f('ix_leads_tenant_id'), 'leads', ['tenant_id'], unique=False)
    
    # Create social_posts table
    op.create_table(
        'social_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.Enum('linkedin', 'facebook', 'instagram', 'twitter', name='socialplatform'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('media_urls', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('practice_area', sa.String(length=100), nullable=True),
        sa.Column('target_audience', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('draft', 'scheduled', 'published', 'failed', name='poststatus'), nullable=False),
        sa.Column('scheduled_time', sa.DateTime(), nullable=True),
        sa.Column('published_time', sa.DateTime(), nullable=True),
        sa.Column('impressions', sa.Integer(), nullable=True, default=0),
        sa.Column('engagements', sa.Integer(), nullable=True, default=0),
        sa.Column('clicks', sa.Integer(), nullable=True, default=0),
        sa.Column('conversions', sa.Integer(), nullable=True, default=0),
        sa.Column('campaign', sa.String(length=100), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('tenant_id', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_social_posts_platform'), 'social_posts', ['platform'], unique=False)
    op.create_index(op.f('ix_social_posts_practice_area'), 'social_posts', ['practice_area'], unique=False)
    op.create_index(op.f('ix_social_posts_status'), 'social_posts', ['status'], unique=False)
    op.create_index(op.f('ix_social_posts_scheduled_time'), 'social_posts', ['scheduled_time'], unique=False)
    op.create_index(op.f('ix_social_posts_campaign'), 'social_posts', ['campaign'], unique=False)
    op.create_index(op.f('ix_social_posts_tenant_id'), 'social_posts', ['tenant_id'], unique=False)
    
    # Create webhook_events table
    op.create_table(
        'webhook_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False, default=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, default=0),
        sa.Column('max_retries', sa.Integer(), nullable=True, default=3),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('tenant_id', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhook_events_event_type'), 'webhook_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_webhook_events_source'), 'webhook_events', ['source'], unique=False)
    op.create_index(op.f('ix_webhook_events_processed'), 'webhook_events', ['processed'], unique=False)
    op.create_index(op.f('ix_webhook_events_created_at'), 'webhook_events', ['created_at'], unique=False)
    op.create_index(op.f('ix_webhook_events_tenant_id'), 'webhook_events', ['tenant_id'], unique=False)


def downgrade():
    """Drop marketing tables."""
    
    # Drop webhook_events table
    op.drop_index(op.f('ix_webhook_events_tenant_id'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_created_at'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_processed'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_source'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_event_type'), table_name='webhook_events')
    op.drop_table('webhook_events')
    
    # Drop social_posts table
    op.drop_index(op.f('ix_social_posts_tenant_id'), table_name='social_posts')
    op.drop_index(op.f('ix_social_posts_campaign'), table_name='social_posts')
    op.drop_index(op.f('ix_social_posts_scheduled_time'), table_name='social_posts')
    op.drop_index(op.f('ix_social_posts_status'), table_name='social_posts')
    op.drop_index(op.f('ix_social_posts_practice_area'), table_name='social_posts')
    op.drop_index(op.f('ix_social_posts_platform'), table_name='social_posts')
    op.drop_table('social_posts')
    
    # Drop leads table
    op.drop_index(op.f('ix_leads_tenant_id'), table_name='leads')
    op.drop_index(op.f('ix_leads_status'), table_name='leads')
    op.drop_index(op.f('ix_leads_contact_email'), table_name='leads')
    op.drop_index(op.f('ix_leads_firm_name'), table_name='leads')
    op.drop_table('leads')
    
    # Drop enums
    sa.Enum(name='leadstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='socialplatform').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='poststatus').drop(op.get_bind(), checkfirst=True)
