"""
Leads API endpoints for HERMES Marketing Command Center
Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.

Provides lead pipeline management endpoints.
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session

from ..database import get_database_session
from ..database.models import Lead, LeadStatus
from ..database.tenant_context import get_tenant_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leads", tags=["leads"])


# Pydantic models for request/response
class LeadCreate(BaseModel):
    """Lead creation request model."""
    firm_name: str = Field(..., min_length=1, max_length=255)
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    status: LeadStatus = LeadStatus.NEW
    firm_size: Optional[str] = None
    practice_areas: Optional[List[str]] = None
    jurisdiction: Optional[str] = None
    pipeline_value: Optional[int] = None
    probability: Optional[int] = Field(None, ge=0, le=100)
    source: Optional[str] = None
    campaign: Optional[str] = None
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    """Lead update request model."""
    firm_name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    status: Optional[LeadStatus] = None
    firm_size: Optional[str] = None
    practice_areas: Optional[List[str]] = None
    jurisdiction: Optional[str] = None
    pipeline_value: Optional[int] = None
    probability: Optional[int] = Field(None, ge=0, le=100)
    source: Optional[str] = None
    campaign: Optional[str] = None
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    """Lead response model."""
    id: int
    firm_name: str
    contact_name: Optional[str]
    contact_email: Optional[EmailStr]
    contact_phone: Optional[str]
    status: LeadStatus
    firm_size: Optional[str]
    practice_areas: Optional[List[str]]
    jurisdiction: Optional[str]
    pipeline_value: Optional[int]
    probability: Optional[int]
    source: Optional[str]
    campaign: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_contacted: Optional[datetime]

    class Config:
        from_attributes = True


@router.post("", response_model=LeadResponse, status_code=201)
async def create_lead(
    lead_data: LeadCreate,
    db: Session = Depends(get_database_session),
    tenant_context=Depends(get_tenant_context),
):
    """Create a new lead.
    
    Args:
        lead_data: Lead creation data
        db: Database session
        tenant_context: Tenant context for isolation
        
    Returns:
        Created lead object
    """
    try:
        lead = Lead(
            firm_name=lead_data.firm_name,
            contact_name=lead_data.contact_name,
            contact_email=lead_data.contact_email,
            contact_phone=lead_data.contact_phone,
            status=lead_data.status,
            firm_size=lead_data.firm_size,
            practice_areas=lead_data.practice_areas,
            jurisdiction=lead_data.jurisdiction,
            pipeline_value=lead_data.pipeline_value,
            probability=lead_data.probability,
            source=lead_data.source,
            campaign=lead_data.campaign,
            notes=lead_data.notes,
            tenant_id=tenant_context.get("tenant_id") if tenant_context else None
        )
        
        db.add(lead)
        db.commit()
        db.refresh(lead)
        
        logger.info(f"Created lead {lead.id}: {lead.firm_name}")
        return lead
        
    except Exception as e:
        logger.error(f"Error creating lead: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create lead")


@router.get("", response_model=List[LeadResponse])
async def list_leads(
    status: Optional[LeadStatus] = Query(None, description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source", max_length=100),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_database_session),
    tenant_context=Depends(get_tenant_context),
):
    """List leads with optional filtering.
    
    Args:
        status: Filter by lead status
        source: Filter by lead source
        limit: Maximum number of results
        offset: Offset for pagination
        db: Database session
        tenant_context: Tenant context for isolation
        
    Returns:
        List of leads
    """
    try:
        query = db.query(Lead)
        
        # Apply tenant filtering
        if tenant_context:
            tenant_id = tenant_context.get("tenant_id")
            if tenant_id:
                query = query.filter(Lead.tenant_id == tenant_id)
        
        # Apply status filter
        if status:
            query = query.filter(Lead.status == status)
        
        # Apply source filter
        if source:
            query = query.filter(Lead.source == source)
        
        # Order and paginate
        leads = query.order_by(Lead.created_at.desc()).offset(offset).limit(limit).all()
        
        return leads
        
    except Exception as e:
        logger.error(f"Error listing leads: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve leads")


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: int,
    db: Session = Depends(get_database_session),
    tenant_context=Depends(get_tenant_context),
):
    """Get a specific lead by ID.
    
    Args:
        lead_id: ID of the lead to retrieve
        db: Database session
        tenant_context: Tenant context for isolation
        
    Returns:
        Lead object
    """
    try:
        query = db.query(Lead).filter(Lead.id == lead_id)
        
        # Apply tenant filtering
        if tenant_context:
            tenant_id = tenant_context.get("tenant_id")
            if tenant_id:
                query = query.filter(Lead.tenant_id == tenant_id)
        
        lead = query.first()
        
        if not lead:
            raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")
        
        return lead
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving lead {lead_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve lead")


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    lead_data: LeadUpdate,
    db: Session = Depends(get_database_session),
    tenant_context=Depends(get_tenant_context),
):
    """Update a lead.
    
    Args:
        lead_id: ID of the lead to update
        lead_data: Updated lead data
        db: Database session
        tenant_context: Tenant context for isolation
        
    Returns:
        Updated lead object
    """
    try:
        query = db.query(Lead).filter(Lead.id == lead_id)
        
        # Apply tenant filtering
        if tenant_context:
            tenant_id = tenant_context.get("tenant_id")
            if tenant_id:
                query = query.filter(Lead.tenant_id == tenant_id)
        
        lead = query.first()
        
        if not lead:
            raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")
        
        # Update fields
        update_data = lead_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lead, field, value)
        
        # Update timestamp
        if lead_data.status and lead_data.status != lead.status:
            lead.last_contacted = datetime.utcnow()
        
        db.commit()
        db.refresh(lead)
        
        logger.info(f"Updated lead {lead_id}")
        return lead
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lead {lead_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update lead")


@router.delete("/{lead_id}", status_code=204)
async def delete_lead(
    lead_id: int,
    db: Session = Depends(get_database_session),
    tenant_context=Depends(get_tenant_context),
):
    """Delete a lead.
    
    Args:
        lead_id: ID of the lead to delete
        db: Database session
        tenant_context: Tenant context for isolation
    """
    try:
        query = db.query(Lead).filter(Lead.id == lead_id)
        
        # Apply tenant filtering
        if tenant_context:
            tenant_id = tenant_context.get("tenant_id")
            if tenant_id:
                query = query.filter(Lead.tenant_id == tenant_id)
        
        lead = query.first()
        
        if not lead:
            raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")
        
        db.delete(lead)
        db.commit()
        
        logger.info(f"Deleted lead {lead_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting lead {lead_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete lead")
