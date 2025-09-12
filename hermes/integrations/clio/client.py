"""Clio API client for data operations."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel

from .auth import ClioAuthHandler, ClioTokens

logger = logging.getLogger(__name__)


class ClioContact(BaseModel):
    """Clio contact model."""
    id: int
    type: str  # Person or Company
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class ClioMatter(BaseModel):
    """Clio matter model."""
    id: int
    display_number: str
    description: str
    status: str
    client: Optional[ClioContact] = None
    responsible_attorney: Optional[ClioContact] = None
    practice_area: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    billable: bool = True
    

class ClioTimeEntry(BaseModel):
    """Clio time entry model."""
    id: int
    date: datetime
    quantity: float  # Hours
    price: Optional[float] = None
    rate: Optional[float] = None
    description: str
    matter: Optional[ClioMatter] = None
    user: Optional[ClioContact] = None
    created_at: datetime
    updated_at: datetime


class ClioDocument(BaseModel):
    """Clio document model."""
    id: int
    name: str
    description: Optional[str] = None
    size: int
    content_type: str
    matter: Optional[ClioMatter] = None
    created_at: datetime
    updated_at: datetime
    url: Optional[str] = None


class ClioActivity(BaseModel):
    """Clio activity model."""
    id: int
    type: str
    description: str
    regarding: Optional[str] = None
    matter: Optional[ClioMatter] = None
    contact: Optional[ClioContact] = None
    created_at: datetime
    updated_at: datetime


class ClioAPIClient:
    """Clio API client for data operations."""
    
    BASE_URL = "https://app.clio.com/api/v4"
    
    def __init__(self, auth_handler: ClioAuthHandler):
        self.auth_handler = auth_handler
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        tokens: ClioTokens,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated API request to Clio.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            tokens: Clio authentication tokens
            params: URL parameters
            data: Form data
            json_data: JSON payload
            
        Returns:
            Response data as dictionary
            
        Raises:
            httpx.HTTPError: If request fails
        """
        # Check if token is expired and refresh if needed
        if self.auth_handler.is_token_expired(tokens):
            tokens = await self.auth_handler.refresh_access_token(tokens.refresh_token)
        
        headers = {
            "Authorization": f"{tokens.token_type} {tokens.access_token}",
            "User-Agent": "HERMES-Legal-AI/1.0",
            "Accept": "application/json",
        }
        
        if json_data:
            headers["Content-Type"] = "application/json"
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data,
                headers=headers
            )
            response.raise_for_status()
            
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            else:
                return {"content": response.content, "headers": dict(response.headers)}
                
        except httpx.HTTPError as e:
            logger.error(f"Clio API request failed: {method} {url} - {e}")
            raise
    
    # Contact Operations
    
    async def get_contacts(
        self, 
        tokens: ClioTokens,
        limit: int = 50,
        offset: int = 0,
        contact_type: Optional[str] = None,
        query: Optional[str] = None
    ) -> List[ClioContact]:
        """Get list of contacts from Clio.
        
        Args:
            tokens: Clio authentication tokens
            limit: Number of contacts to return (max 200)
            offset: Offset for pagination
            contact_type: Filter by contact type ("Person" or "Company")
            query: Search query
            
        Returns:
            List of ClioContact objects
        """
        params = {
            "limit": min(limit, 200),
            "offset": offset,
        }
        
        if contact_type:
            params["type"] = contact_type
        
        if query:
            params["query"] = query
        
        response = await self._make_request("GET", "/contacts", tokens, params=params)
        
        contacts = []
        for contact_data in response.get("contacts", []):
            contacts.append(ClioContact(**contact_data))
        
        return contacts
    
    async def get_contact(self, tokens: ClioTokens, contact_id: int) -> Optional[ClioContact]:
        """Get specific contact by ID.
        
        Args:
            tokens: Clio authentication tokens
            contact_id: Contact ID
            
        Returns:
            ClioContact object or None if not found
        """
        try:
            response = await self._make_request("GET", f"/contacts/{contact_id}", tokens)
            return ClioContact(**response["contact"])
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def create_contact(
        self, 
        tokens: ClioTokens, 
        contact_data: Dict[str, Any]
    ) -> ClioContact:
        """Create new contact in Clio.
        
        Args:
            tokens: Clio authentication tokens
            contact_data: Contact information
            
        Returns:
            Created ClioContact object
        """
        response = await self._make_request(
            "POST", 
            "/contacts", 
            tokens,
            json_data={"contact": contact_data}
        )
        return ClioContact(**response["contact"])
    
    async def update_contact(
        self, 
        tokens: ClioTokens, 
        contact_id: int,
        contact_data: Dict[str, Any]
    ) -> ClioContact:
        """Update existing contact.
        
        Args:
            tokens: Clio authentication tokens
            contact_id: Contact ID
            contact_data: Updated contact information
            
        Returns:
            Updated ClioContact object
        """
        response = await self._make_request(
            "PATCH", 
            f"/contacts/{contact_id}", 
            tokens,
            json_data={"contact": contact_data}
        )
        return ClioContact(**response["contact"])
    
    # Matter Operations
    
    async def get_matters(
        self, 
        tokens: ClioTokens,
        limit: int = 50,
        offset: int = 0,
        client_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[ClioMatter]:
        """Get list of matters from Clio.
        
        Args:
            tokens: Clio authentication tokens
            limit: Number of matters to return (max 200)
            offset: Offset for pagination
            client_id: Filter by client ID
            status: Filter by status
            
        Returns:
            List of ClioMatter objects
        """
        params = {
            "limit": min(limit, 200),
            "offset": offset,
        }
        
        if client_id:
            params["client_id"] = client_id
        
        if status:
            params["status"] = status
        
        response = await self._make_request("GET", "/matters", tokens, params=params)
        
        matters = []
        for matter_data in response.get("matters", []):
            matters.append(ClioMatter(**matter_data))
        
        return matters
    
    async def get_matter(self, tokens: ClioTokens, matter_id: int) -> Optional[ClioMatter]:
        """Get specific matter by ID.
        
        Args:
            tokens: Clio authentication tokens
            matter_id: Matter ID
            
        Returns:
            ClioMatter object or None if not found
        """
        try:
            response = await self._make_request("GET", f"/matters/{matter_id}", tokens)
            return ClioMatter(**response["matter"])
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def create_matter(
        self, 
        tokens: ClioTokens, 
        matter_data: Dict[str, Any]
    ) -> ClioMatter:
        """Create new matter in Clio.
        
        Args:
            tokens: Clio authentication tokens
            matter_data: Matter information
            
        Returns:
            Created ClioMatter object
        """
        response = await self._make_request(
            "POST", 
            "/matters", 
            tokens,
            json_data={"matter": matter_data}
        )
        return ClioMatter(**response["matter"])
    
    # Time Entry Operations
    
    async def get_time_entries(
        self, 
        tokens: ClioTokens,
        limit: int = 50,
        offset: int = 0,
        matter_id: Optional[int] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ClioTimeEntry]:
        """Get list of time entries from Clio.
        
        Args:
            tokens: Clio authentication tokens
            limit: Number of entries to return (max 200)
            offset: Offset for pagination
            matter_id: Filter by matter ID
            user_id: Filter by user ID  
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            List of ClioTimeEntry objects
        """
        params = {
            "limit": min(limit, 200),
            "offset": offset,
        }
        
        if matter_id:
            params["matter_id"] = matter_id
        
        if user_id:
            params["user_id"] = user_id
        
        if start_date:
            params["date_since"] = start_date.isoformat()
        
        if end_date:
            params["date_until"] = end_date.isoformat()
        
        response = await self._make_request("GET", "/time_entries", tokens, params=params)
        
        time_entries = []
        for entry_data in response.get("time_entries", []):
            time_entries.append(ClioTimeEntry(**entry_data))
        
        return time_entries
    
    async def create_time_entry(
        self, 
        tokens: ClioTokens, 
        time_entry_data: Dict[str, Any]
    ) -> ClioTimeEntry:
        """Create new time entry in Clio.
        
        Args:
            tokens: Clio authentication tokens
            time_entry_data: Time entry information
            
        Returns:
            Created ClioTimeEntry object
        """
        response = await self._make_request(
            "POST", 
            "/time_entries", 
            tokens,
            json_data={"time_entry": time_entry_data}
        )
        return ClioTimeEntry(**response["time_entry"])
    
    # Document Operations
    
    async def get_documents(
        self, 
        tokens: ClioTokens,
        limit: int = 50,
        offset: int = 0,
        matter_id: Optional[int] = None
    ) -> List[ClioDocument]:
        """Get list of documents from Clio.
        
        Args:
            tokens: Clio authentication tokens
            limit: Number of documents to return (max 200)
            offset: Offset for pagination
            matter_id: Filter by matter ID
            
        Returns:
            List of ClioDocument objects
        """
        params = {
            "limit": min(limit, 200),
            "offset": offset,
        }
        
        if matter_id:
            params["matter_id"] = matter_id
        
        response = await self._make_request("GET", "/documents", tokens, params=params)
        
        documents = []
        for doc_data in response.get("documents", []):
            documents.append(ClioDocument(**doc_data))
        
        return documents
    
    async def upload_document(
        self, 
        tokens: ClioTokens, 
        file_data: bytes,
        filename: str,
        matter_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> ClioDocument:
        """Upload document to Clio.
        
        Args:
            tokens: Clio authentication tokens
            file_data: File content as bytes
            filename: Name of the file
            matter_id: Matter to associate with
            description: Document description
            
        Returns:
            Created ClioDocument object
        """
        # First, create the document record
        document_data = {
            "name": filename,
            "description": description or "",
        }
        
        if matter_id:
            document_data["matter"] = {"id": matter_id}
        
        response = await self._make_request(
            "POST", 
            "/documents", 
            tokens,
            json_data={"document": document_data}
        )
        
        document = ClioDocument(**response["document"])
        
        # Then upload the file content (this would require additional API calls)
        # Implementation details depend on Clio's file upload process
        
        return document
    
    # Activity Operations
    
    async def get_activities(
        self, 
        tokens: ClioTokens,
        limit: int = 50,
        offset: int = 0,
        matter_id: Optional[int] = None,
        contact_id: Optional[int] = None
    ) -> List[ClioActivity]:
        """Get list of activities from Clio.
        
        Args:
            tokens: Clio authentication tokens
            limit: Number of activities to return (max 200)
            offset: Offset for pagination
            matter_id: Filter by matter ID
            contact_id: Filter by contact ID
            
        Returns:
            List of ClioActivity objects
        """
        params = {
            "limit": min(limit, 200),
            "offset": offset,
        }
        
        if matter_id:
            params["matter_id"] = matter_id
        
        if contact_id:
            params["contact_id"] = contact_id
        
        response = await self._make_request("GET", "/activities", tokens, params=params)
        
        activities = []
        for activity_data in response.get("activities", []):
            activities.append(ClioActivity(**activity_data))
        
        return activities
    
    async def create_activity(
        self, 
        tokens: ClioTokens, 
        activity_data: Dict[str, Any]
    ) -> ClioActivity:
        """Create new activity in Clio.
        
        Args:
            tokens: Clio authentication tokens
            activity_data: Activity information
            
        Returns:
            Created ClioActivity object
        """
        response = await self._make_request(
            "POST", 
            "/activities", 
            tokens,
            json_data={"activity": activity_data}
        )
        return ClioActivity(**response["activity"])
    
    # User Information
    
    async def get_current_user(self, tokens: ClioTokens) -> Dict[str, Any]:
        """Get current user information.
        
        Args:
            tokens: Clio authentication tokens
            
        Returns:
            User information dictionary
        """
        response = await self._make_request("GET", "/users/who_am_i", tokens)
        return response.get("user", {})