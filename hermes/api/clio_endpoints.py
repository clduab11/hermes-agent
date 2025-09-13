"""
Clio CRM API endpoints for HERMES legal integration
Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.

Provides complete Clio OAuth 2.0 integration with CRUD operations for:
- Contacts (clients and prospects)
- Matters (cases and legal matters)
- Activities (appointments, tasks, communications)
- Documents (file management and sharing)
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date
import logging
import asyncio

from ..auth.middleware import get_current_user, require_permission
from ..integrations.clio.client import ClioAPIClient, ClioClient
from ..integrations.clio.auth import ClioAuthHandler
from ..database.tenant_context import get_tenant_context
from ..database import get_database_session
from ..database.security import SecureAsyncSession
from ..integrations.clio.token_repository import upsert_clio_tokens, get_clio_tokens, delete_clio_tokens

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clio", tags=["clio-integration"])

# Pydantic models for Clio entities
class ContactBase(BaseModel):
    """Base model for Clio contacts."""
    name: str = Field(..., description="Full name of the contact")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[Dict[str, str]] = Field(None, description="Address information")
    type: str = Field("person", description="Contact type: person, company")
    client_type: Optional[str] = Field(None, description="Client, prospect, etc.")

class ContactCreate(ContactBase):
    """Model for creating new contacts."""
    pass

class ContactUpdate(BaseModel):
    """Model for updating contacts."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    client_type: Optional[str] = None

class ContactResponse(ContactBase):
    """Response model for contacts."""
    id: str
    created_at: datetime
    updated_at: datetime

class MatterBase(BaseModel):
    """Base model for Clio matters."""
    display_number: str = Field(..., description="Matter number")
    description: str = Field(..., description="Matter description")
    client_id: str = Field(..., description="Client ID")
    practice_area: Optional[str] = Field(None, description="Practice area")
    status: str = Field("open", description="Matter status")
    billing_method: Optional[str] = Field(None, description="Billing method")

class MatterCreate(MatterBase):
    """Model for creating new matters."""
    pass

class MatterUpdate(BaseModel):
    """Model for updating matters."""
    description: Optional[str] = None
    status: Optional[str] = None
    practice_area: Optional[str] = None
    billing_method: Optional[str] = None

class MatterResponse(MatterBase):
    """Response model for matters."""
    id: str
    created_at: datetime
    updated_at: datetime

class ActivityBase(BaseModel):
    """Base model for Clio activities."""
    type: str = Field(..., description="Activity type: call, email, appointment")
    description: str = Field(..., description="Activity description")
    date: date = Field(..., description="Activity date")
    time: Optional[str] = Field(None, description="Activity time")
    contact_id: Optional[str] = Field(None, description="Related contact ID")
    matter_id: Optional[str] = Field(None, description="Related matter ID")

class ActivityCreate(ActivityBase):
    """Model for creating new activities."""
    pass

class ActivityResponse(ActivityBase):
    """Response model for activities."""
    id: str
    created_at: datetime
    updated_at: datetime

class DocumentBase(BaseModel):
    """Base model for Clio documents."""
    name: str = Field(..., description="Document name")
    description: Optional[str] = Field(None, description="Document description")
    matter_id: Optional[str] = Field(None, description="Related matter ID")
    contact_id: Optional[str] = Field(None, description="Related contact ID")

class DocumentCreate(DocumentBase):
    """Model for creating new documents."""
    file_data: Optional[str] = Field(None, description="Base64 encoded file data")
    file_type: Optional[str] = Field(None, description="File MIME type")

class DocumentResponse(DocumentBase):
    """Response model for documents."""
    id: str
    created_at: datetime
    updated_at: datetime
    file_url: Optional[str] = Field(None, description="Download URL")

# Helper function to get authenticated Clio client
async def get_clio_client(
    current_user = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context)
) -> ClioClient:
    """Return an authenticated Clio API client or 401 if not authorized yet."""
    db_session = await get_database_session()
    if not db_session:
        raise HTTPException(status_code=503, detail="Database not configured")
    async with SecureAsyncSession(db_session) as session:
        tokens = await get_clio_tokens(session, tenant_context.tenant_id, current_user["id"])
        if not tokens:
            raise HTTPException(status_code=401, detail="Clio not authorized for this tenant/user")
    # Return a lightweight client bound to tokens
    return ClioClient(auth_handler=ClioAuthHandler(), tokens=tokens)

# OAuth endpoints
@router.get("/oauth/authorize")
async def authorize_clio(
    current_user = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context)
):
    """Start Clio OAuth authorization flow."""
    try:
        handler = ClioAuthHandler()
        auth_url, state = handler.generate_authorization_url(tenant_id=tenant_context.tenant_id)
        return {"authorization_url": auth_url}
    except Exception as e:
        logger.error(f"OAuth authorization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OAuth authorization"
        )

@router.get("/oauth/callback")
async def handle_oauth_callback_get(
    code: str,
    state: str,
    current_user = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context)
):
    """Handle Clio OAuth callback (GET) and exchange code for tokens."""
    try:
        db_session = await get_database_session()
        if not db_session:
            raise HTTPException(status_code=503, detail="Database not configured")
        handler = ClioAuthHandler()
        tokens = await handler.exchange_code_for_tokens(
            code=code,
            state=state,
            tenant_id=tenant_context.tenant_id,
        )
        # Persist tokens for tenant/user
        async with SecureAsyncSession(db_session) as session:
            await upsert_clio_tokens(session, tenant_context.tenant_id, current_user["id"], tokens)
        return {"status": "success", "message": "Clio integration activated"}
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to complete OAuth authorization"
        )

@router.post("/oauth/callback")
async def handle_oauth_callback_post(
    code: str,
    state: str,
    current_user = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context)
):
    """Handle Clio OAuth callback (POST) for compatibility."""
    return await handle_oauth_callback_get(code, state, current_user, tenant_context)

# Support trailing slash variant some configurations may require
@router.get("/oauth/callback/")
async def handle_oauth_callback_get_slash(
    code: str,
    state: str,
    current_user = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context)
):
    return await handle_oauth_callback_get(code, state, current_user, tenant_context)

# Contact endpoints
@router.get("/contacts", response_model=List[ContactResponse])
async def list_contacts(
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    client: ClioClient = Depends(get_clio_client),
    _: None = Depends(require_permission("clio:read"))
):
    """List Clio contacts with pagination and search."""
    try:
        contacts = await client.list_contacts(
            limit=limit,
            offset=offset,
            search=search
        )
        return contacts
    except Exception as e:
        logger.error(f"Error listing contacts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve contacts from Clio"
        )

@router.post("/contacts", response_model=ContactResponse)
async def create_contact(
    contact: ContactCreate,
    client: ClioClient = Depends(get_clio_client),
    _: None = Depends(require_permission("clio:write"))
):
    """Create a new Clio contact."""
    try:
        new_contact = await client.create_contact(contact.model_dump())
        return new_contact
    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create contact in Clio"
        )

@router.get("/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: str,
    client: ClioClient = Depends(get_clio_client),
    _: None = Depends(require_permission("clio:read"))
):
    """Get a specific Clio contact by ID."""
    try:
        contact = await client.get_contact(contact_id)
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        return contact
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving contact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve contact from Clio"
        )

@router.put("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    contact_update: ContactUpdate,
    client: ClioClient = Depends(get_clio_client),
    _: None = Depends(require_permission("clio:write"))
):
    """Update a Clio contact."""
    try:
        updated_contact = await client.update_contact(
            contact_id, 
            contact_update.model_dump(exclude_none=True)
        )
        return updated_contact
    except Exception as e:
        logger.error(f"Error updating contact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update contact in Clio"
        )

# Matter endpoints
@router.get("/matters", response_model=List[MatterResponse])
async def list_matters(
    limit: int = 50,
    offset: int = 0,
    client_id: Optional[str] = None,
    status: Optional[str] = None,
    client: ClioClient = Depends(get_clio_client),
    _: None = Depends(require_permission("clio:read"))
):
    """List Clio matters with filtering."""
    try:
        matters = await client.list_matters(
            limit=limit,
            offset=offset,
            client_id=client_id,
            status=status
        )
        return matters
    except Exception as e:
        logger.error(f"Error listing matters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve matters from Clio"
        )

@router.post("/matters", response_model=MatterResponse)
async def create_matter(
    matter: MatterCreate,
    client: ClioClient = Depends(get_clio_client),
    _: None = Depends(require_permission("clio:write"))
):
    """Create a new Clio matter."""
    try:
        new_matter = await client.create_matter(matter.model_dump())
        return new_matter
    except Exception as e:
        logger.error(f"Error creating matter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create matter in Clio"
        )

@router.get("/matters/{matter_id}", response_model=MatterResponse)
async def get_matter(
    matter_id: str,
    client: ClioClient = Depends(get_clio_client),
    _: None = Depends(require_permission("clio:read"))
):
    """Get a specific Clio matter by ID."""
    try:
        matter = await client.get_matter(matter_id)
        if not matter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Matter not found"
            )
        return matter
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving matter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve matter from Clio"
        )

@router.put("/matters/{matter_id}", response_model=MatterResponse)
async def update_matter(
    matter_id: str,
    matter_update: MatterUpdate,
    client: ClioClient = Depends(get_clio_client),
    _: None = Depends(require_permission("clio:write"))
):
    """Update a Clio matter."""
    try:
        updated_matter = await client.update_matter(
            matter_id,
            matter_update.model_dump(exclude_none=True)
        )
        return updated_matter
    except Exception as e:
        logger.error(f"Error updating matter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update matter in Clio"
        )

# Activity endpoints
@router.get("/activities", response_model=List[ActivityResponse])
async def list_activities(
    limit: int = 50,
    offset: int = 0,
    contact_id: Optional[str] = None,
    matter_id: Optional[str] = None,
    activity_type: Optional[str] = None,
    client: ClioClient = Depends(get_clio_client),
    _: None = Depends(require_permission("clio:read"))
):
    """List Clio activities with filtering."""
    try:
        activities = await client.list_activities(
            limit=limit,
            offset=offset,
            contact_id=contact_id,
            matter_id=matter_id,
            activity_type=activity_type
        )
        return activities
    except Exception as e:
        logger.error(f"Error listing activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activities from Clio"
        )

@router.post("/activities", response_model=ActivityResponse)
async def create_activity(
    activity: ActivityCreate,
    client: ClioClient = Depends(get_clio_client),
    _: None = Depends(require_permission("clio:write"))
):
    """Create a new Clio activity."""
    try:
        new_activity = await client.create_activity(activity.model_dump())
        return new_activity
    except Exception as e:
        logger.error(f"Error creating activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create activity in Clio"
        )

# Document endpoints
@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    limit: int = 50,
    offset: int = 0,
    matter_id: Optional[str] = None,
    contact_id: Optional[str] = None,
    client: ClioClient = Depends(get_clio_client),
    _: None = Depends(require_permission("clio:read"))
):
    """List Clio documents with filtering."""
    try:
        documents = await client.list_documents(
            limit=limit,
            offset=offset,
            matter_id=matter_id,
            contact_id=contact_id
        )
        return documents
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents from Clio"
        )

@router.post("/documents", response_model=DocumentResponse)
async def create_document(
    document: DocumentCreate,
    client: ClioClient = Depends(get_clio_client),
    _: None = Depends(require_permission("clio:write"))
):
    """Create a new Clio document."""
    try:
        new_document = await client.create_document(document.model_dump())
        return new_document
    except Exception as e:
        logger.error(f"Error creating document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create document in Clio"
        )

# Bulk operations
@router.post("/bulk/import-contacts")
async def bulk_import_contacts(
    contacts: List[ContactCreate],
    background_tasks: BackgroundTasks,
    client: ClioClient = Depends(get_clio_client),
    _: None = Depends(require_permission("clio:write"))
):
    """Bulk import contacts to Clio."""
    try:
        # Start background task for bulk import
        background_tasks.add_task(
            client.bulk_import_contacts,
            [contact.model_dump() for contact in contacts]
        )
        return {
            "status": "started",
            "message": f"Bulk import of {len(contacts)} contacts started",
            "total_contacts": len(contacts)
        }
    except Exception as e:
        logger.error(f"Error starting bulk import: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start bulk import"
        )

@router.get("/sync-status")
async def get_sync_status(
    client: ClioClient = Depends(get_clio_client),
    _: None = Depends(require_permission("clio:read"))
):
    """Get Clio synchronization status."""
    try:
        sync_status = await client.get_sync_status()
        return sync_status
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sync status"
        )

# Health check endpoint
@router.get("/health")
async def clio_health_check(
    client: ClioClient = Depends(get_clio_client)
):
    """Check Clio API connectivity and authentication status."""
    try:
        health = await client.health_check()
        return {
            "status": "healthy" if health else "unhealthy",
            "clio_api": "connected" if health else "disconnected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Clio health check failed: {e}")
        return {
            "status": "unhealthy",
            "clio_api": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
@router.delete("/admin/tokens")
async def revoke_clio_tokens(
    target_user_id: Optional[str] = None,
    revoke_remote: bool = True,
    current_user = Depends(get_current_user),
    tenant_context = Depends(get_tenant_context),
    _: None = Depends(require_permission("clio:admin")),
):
    """Admin: revoke stored Clio tokens for a user (or self if omitted).

    - If revoke_remote is true, attempts to revoke the refresh token with Clio.
    - Always removes tokens from local storage.
    """
    db_session = await get_database_session()
    if not db_session:
        raise HTTPException(status_code=503, detail="Database not configured")
    user_id = target_user_id or current_user["id"]
    handler = ClioAuthHandler()
    async with SecureAsyncSession(db_session) as session:
        tokens = await get_clio_tokens(session, tenant_context.tenant_id, user_id)
        if not tokens:
            return {"status": "not_found", "message": "No tokens stored"}
        if revoke_remote:
            try:
                await handler.revoke_token(tokens.refresh_token, token_type="refresh_token")
            except Exception as e:
                logger.warning(f"Remote revoke failed: {e}")
        deleted = await delete_clio_tokens(session, tenant_context.tenant_id, user_id)
        return {"status": "revoked", "deleted": deleted}
