"""
Analytics Service for HERMES Marketing Command Center
Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.

Handles metrics calculation and reporting for marketing analytics.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database.models import Lead, LeadStatus, SocialPost, PostStatus, WebhookEvent

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for marketing analytics and reporting."""
    
    def __init__(self, db_session: Session):
        """Initialize analytics service.
        
        Args:
            db_session: Database session for analytics queries
        """
        self.db = db_session
    
    async def get_funnel_metrics(
        self,
        tenant_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Calculate conversion funnel metrics.
        
        Args:
            tenant_id: Filter by tenant ID
            days: Number of days to include in calculation
            
        Returns:
            Dictionary with funnel metrics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(Lead)
        if tenant_id:
            query = query.filter(Lead.tenant_id == tenant_id)
        query = query.filter(Lead.created_at >= start_date)
        
        # Count leads by status
        total_leads = query.count()
        contacted = query.filter(Lead.status.in_([
            LeadStatus.CONTACTED, LeadStatus.QUALIFIED, 
            LeadStatus.DEMO_SCHEDULED, LeadStatus.PROPOSAL_SENT,
            LeadStatus.NEGOTIATING, LeadStatus.WON
        ])).count()
        qualified = query.filter(Lead.status.in_([
            LeadStatus.QUALIFIED, LeadStatus.DEMO_SCHEDULED,
            LeadStatus.PROPOSAL_SENT, LeadStatus.NEGOTIATING, LeadStatus.WON
        ])).count()
        demo_scheduled = query.filter(Lead.status.in_([
            LeadStatus.DEMO_SCHEDULED, LeadStatus.PROPOSAL_SENT,
            LeadStatus.NEGOTIATING, LeadStatus.WON
        ])).count()
        proposal_sent = query.filter(Lead.status.in_([
            LeadStatus.PROPOSAL_SENT, LeadStatus.NEGOTIATING, LeadStatus.WON
        ])).count()
        won = query.filter(Lead.status == LeadStatus.WON).count()
        
        # Calculate conversion rates
        conversion_rate = (won / total_leads * 100) if total_leads > 0 else 0
        
        return {
            "total_leads": total_leads,
            "contacted": contacted,
            "qualified": qualified,
            "demo_scheduled": demo_scheduled,
            "proposal_sent": proposal_sent,
            "won": won,
            "conversion_rate": round(conversion_rate, 2),
            "period_days": days
        }
    
    async def get_pipeline_value(
        self,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate total pipeline value.
        
        Args:
            tenant_id: Filter by tenant ID
            
        Returns:
            Dictionary with pipeline value metrics
        """
        query = self.db.query(Lead).filter(
            Lead.status.in_([
                LeadStatus.QUALIFIED, LeadStatus.DEMO_SCHEDULED,
                LeadStatus.PROPOSAL_SENT, LeadStatus.NEGOTIATING
            ])
        )
        
        if tenant_id:
            query = query.filter(Lead.tenant_id == tenant_id)
        
        # Calculate total pipeline value
        result = query.with_entities(
            func.sum(Lead.pipeline_value).label('total_value'),
            func.avg(Lead.probability).label('avg_probability'),
            func.count(Lead.id).label('count')
        ).first()
        
        total_value = result.total_value or 0
        avg_probability = result.avg_probability or 0
        count = result.count or 0
        
        # Calculate weighted pipeline value
        weighted_value = int(total_value * (avg_probability / 100)) if avg_probability > 0 else 0
        
        return {
            "total_pipeline_value": int(total_value),
            "weighted_pipeline_value": weighted_value,
            "average_probability": round(avg_probability, 2),
            "active_opportunities": count
        }
    
    async def get_social_performance(
        self,
        tenant_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get social media performance metrics.
        
        Args:
            tenant_id: Filter by tenant ID
            days: Number of days to include in calculation
            
        Returns:
            Dictionary with social media metrics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(SocialPost).filter(
            SocialPost.created_at >= start_date
        )
        
        if tenant_id:
            query = query.filter(SocialPost.tenant_id == tenant_id)
        
        # Aggregate metrics
        result = query.with_entities(
            func.count(SocialPost.id).label('total_posts'),
            func.sum(SocialPost.impressions).label('total_impressions'),
            func.sum(SocialPost.engagements).label('total_engagements'),
            func.sum(SocialPost.clicks).label('total_clicks'),
            func.sum(SocialPost.conversions).label('total_conversions')
        ).first()
        
        total_posts = result.total_posts or 0
        total_impressions = result.total_impressions or 0
        total_engagements = result.total_engagements or 0
        total_clicks = result.total_clicks or 0
        total_conversions = result.total_conversions or 0
        
        # Calculate engagement rate
        engagement_rate = (total_engagements / total_impressions * 100) if total_impressions > 0 else 0
        click_rate = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        
        # Count by status
        published = query.filter(SocialPost.status == PostStatus.PUBLISHED).count()
        scheduled = query.filter(SocialPost.status == PostStatus.SCHEDULED).count()
        draft = query.filter(SocialPost.status == PostStatus.DRAFT).count()
        
        return {
            "total_posts": total_posts,
            "published": published,
            "scheduled": scheduled,
            "draft": draft,
            "total_impressions": int(total_impressions),
            "total_engagements": int(total_engagements),
            "total_clicks": int(total_clicks),
            "total_conversions": int(total_conversions),
            "engagement_rate": round(engagement_rate, 2),
            "click_rate": round(click_rate, 2),
            "conversion_rate": round(conversion_rate, 2),
            "period_days": days
        }
    
    async def get_roi_metrics(
        self,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate ROI metrics.
        
        Args:
            tenant_id: Filter by tenant ID
            
        Returns:
            Dictionary with ROI metrics
        """
        # Calculate won deals value
        query = self.db.query(Lead).filter(Lead.status == LeadStatus.WON)
        
        if tenant_id:
            query = query.filter(Lead.tenant_id == tenant_id)
        
        result = query.with_entities(
            func.sum(Lead.pipeline_value).label('total_revenue'),
            func.count(Lead.id).label('won_deals')
        ).first()
        
        total_revenue = result.total_revenue or 0
        won_deals = result.won_deals or 0
        
        # Estimated cost savings from automation
        # Based on typical law firm metrics:
        # - $50/hour for administrative staff
        # - 3 hours saved per lead on average
        leads_processed = self.db.query(Lead).filter(
            Lead.tenant_id == tenant_id if tenant_id else True
        ).count()
        
        cost_savings = leads_processed * 3 * 50  # leads * hours * hourly_rate
        
        # Calculate annual projection
        annual_revenue = int(total_revenue * 12)  # Assume monthly pipeline value
        annual_savings = int(cost_savings * 12)
        
        return {
            "monthly_revenue": int(total_revenue),
            "annual_revenue": annual_revenue,
            "won_deals": won_deals,
            "cost_savings": cost_savings,
            "annual_savings": annual_savings,
            "total_leads_processed": leads_processed,
            "roi_percentage": round((annual_savings / 2497) * 100, 2) if annual_savings > 0 else 0  # Using professional tier pricing
        }
    
    async def get_dashboard_metrics(
        self,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics.
        
        Args:
            tenant_id: Filter by tenant ID
            
        Returns:
            Dictionary with all dashboard metrics
        """
        funnel = await self.get_funnel_metrics(tenant_id=tenant_id)
        pipeline = await self.get_pipeline_value(tenant_id=tenant_id)
        social = await self.get_social_performance(tenant_id=tenant_id)
        roi = await self.get_roi_metrics(tenant_id=tenant_id)
        
        return {
            "funnel": funnel,
            "pipeline": pipeline,
            "social": social,
            "roi": roi,
            "generated_at": datetime.utcnow().isoformat()
        }
