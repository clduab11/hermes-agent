"""
Social Media API endpoints for HERMES Marketing Command Center
Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.

Provides social media post management endpoints.
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_database_session
from ..database.models import SocialPost, SocialPlatform, PostStatus
from ..database.tenant_context import get_tenant_context
from ..services.social_service import SocialService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/social", tags=["social"])


# Pydantic models
class SocialPostCreate(BaseModel):
    """Social post creation request model."""
    platform: SocialPlatform
    content: str = Field(..., min_length=1)
    practice_area: Optional[str] = None
    target_audience: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    media_urls: Optional[List[str]] = None
    campaign: Optional[str] = None
    tags: Optional[List[str]] = None


class SocialPostResponse(BaseModel):
    """Social post response model."""
    id: int
    platform: SocialPlatform
    content: str
    practice_area: Optional[str]
    target_audience: Optional[str]
    status: PostStatus
    scheduled_time: Optional[datetime]
    published_time: Optional[datetime]
    impressions: int
    engagements: int
    clicks: int
    conversions: int
    campaign: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContentGenerationRequest(BaseModel):
    """Content generation request model."""
    platform: SocialPlatform
    practice_area: str
    content_type: str = "thought_leadership"


class ContentGenerationResponse(BaseModel):
    """Content generation response model."""
    content: str
    platform: SocialPlatform
    practice_area: str


@router.post("/posts", response_model=SocialPostResponse, status_code=201)
async def create_post(
    post_data: SocialPostCreate,
    db: Session = Depends(get_database_session),
    tenant_context=Depends(get_tenant_context),
):
    """Create a new social media post."""
    try:
        service = SocialService(db)
        post = await service.create_post(
            platform=post_data.platform,
            content=post_data.content,
            practice_area=post_data.practice_area,
            scheduled_time=post_data.scheduled_time,
            tenant_id=tenant_context.get("tenant_id") if tenant_context else None,
            target_audience=post_data.target_audience,
            media_urls=post_data.media_urls,
            campaign=post_data.campaign,
            tags=post_data.tags
        )
        
        return post
        
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts", response_model=List[SocialPostResponse])
async def list_posts(
    platform: Optional[SocialPlatform] = Query(None),
    status: Optional[PostStatus] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_database_session),
    tenant_context=Depends(get_tenant_context),
):
    """List social media posts."""
    try:
        service = SocialService(db)
        posts = await service.get_posts(
            platform=platform,
            status=status,
            tenant_id=tenant_context.get("tenant_id") if tenant_context else None,
            limit=limit
        )
        
        return posts
        
    except Exception as e:
        logger.error(f"Error listing posts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts/{post_id}", response_model=SocialPostResponse)
async def get_post(
    post_id: int,
    db: Session = Depends(get_database_session),
    tenant_context=Depends(get_tenant_context),
):
    """Get a specific social media post."""
    try:
        query = db.query(SocialPost).filter(SocialPost.id == post_id)
        
        if tenant_context:
            tenant_id = tenant_context.get("tenant_id")
            if tenant_id:
                query = query.filter(SocialPost.tenant_id == tenant_id)
        
        post = query.first()
        
        if not post:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found")
        
        return post
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving post {post_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/posts/{post_id}/schedule", response_model=SocialPostResponse)
async def schedule_post(
    post_id: int,
    scheduled_time: datetime,
    db: Session = Depends(get_database_session),
    tenant_context=Depends(get_tenant_context),
):
    """Schedule a post for publication."""
    try:
        service = SocialService(db)
        post = await service.schedule_post(post_id, scheduled_time)
        
        return post
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error scheduling post {post_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/posts/{post_id}/publish", response_model=SocialPostResponse)
async def publish_post(
    post_id: int,
    db: Session = Depends(get_database_session),
    tenant_context=Depends(get_tenant_context),
):
    """Mark a post as published."""
    try:
        service = SocialService(db)
        post = await service.publish_post(post_id)
        
        return post
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error publishing post {post_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=ContentGenerationResponse)
async def generate_content(
    request: ContentGenerationRequest,
    db: Session = Depends(get_database_session),
):
    """Generate AI-powered content for social media."""
    try:
        service = SocialService(db)
        content = await service.generate_content(
            platform=request.platform,
            practice_area=request.practice_area,
            content_type=request.content_type
        )
        
        return ContentGenerationResponse(
            content=content,
            platform=request.platform,
            practice_area=request.practice_area
        )
        
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
