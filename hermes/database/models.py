"""
Database models for HERMES Marketing Command Center
Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.

Models for leads, social posts, and webhook events.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class LeadStatus(str, enum.Enum):
    """Lead status enumeration."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    DEMO_SCHEDULED = "demo_scheduled"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATING = "negotiating"
    WON = "won"
    LOST = "lost"


class SocialPlatform(str, enum.Enum):
    """Social media platform enumeration."""
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"


class PostStatus(str, enum.Enum):
    """Social post status enumeration."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class Lead(Base):
    """Law firm prospect tracking."""
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    firm_name = Column(String(255), nullable=False, index=True)
    contact_name = Column(String(255))
    contact_email = Column(String(255), index=True)
    contact_phone = Column(String(50))
    
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW, nullable=False, index=True)
    
    # Firm details
    firm_size = Column(String(50))  # "1-10", "11-50", "50+"
    practice_areas = Column(JSON)  # List of practice areas
    jurisdiction = Column(String(100))
    
    # Pipeline tracking
    pipeline_value = Column(Integer)  # Estimated monthly contract value
    probability = Column(Integer)  # Win probability percentage
    expected_close_date = Column(DateTime)
    
    # Source tracking
    source = Column(String(100))  # "website", "referral", "social", etc.
    campaign = Column(String(100))
    
    # Notes and metadata
    notes = Column(Text)
    metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_contacted = Column(DateTime)
    
    # Tenant isolation
    tenant_id = Column(String(100), index=True)


class SocialPost(Base):
    """Social media content scheduling."""
    __tablename__ = "social_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Content
    platform = Column(SQLEnum(SocialPlatform), nullable=False, index=True)
    content = Column(Text, nullable=False)
    media_urls = Column(JSON)  # List of image/video URLs
    
    # Targeting
    practice_area = Column(String(100), index=True)
    target_audience = Column(String(100))
    
    # Scheduling
    status = Column(SQLEnum(PostStatus), default=PostStatus.DRAFT, nullable=False, index=True)
    scheduled_time = Column(DateTime, index=True)
    published_time = Column(DateTime)
    
    # Performance
    impressions = Column(Integer, default=0)
    engagements = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    
    # Metadata
    campaign = Column(String(100), index=True)
    tags = Column(JSON)  # List of tags
    metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Tenant isolation
    tenant_id = Column(String(100), index=True)


class WebhookEvent(Base):
    """Integration event logging for Zapier and other webhooks."""
    __tablename__ = "webhook_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    source = Column(String(100), nullable=False, index=True)  # "zapier", "clio", etc.
    
    # Payload
    payload = Column(JSON, nullable=False)
    
    # Processing
    processed = Column(Boolean, default=False, nullable=False, index=True)
    processed_at = Column(DateTime)
    error_message = Column(Text)
    
    # Retry tracking
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Metadata
    metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Tenant isolation
    tenant_id = Column(String(100), index=True)
