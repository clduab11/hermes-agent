"""
Mem0 data models following September 2025 best practices
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MemoryNode(BaseModel):
    """Memory node in the Mem0 knowledge graph"""

    id: Optional[str] = None
    user_id: str = Field(..., description="User or session identifier")
    memory_type: str = Field(..., description="Type of memory: fact, event, preference")
    content: str = Field(..., description="Memory content")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0)


class MemoryQuery(BaseModel):
    """Query for retrieving memories"""

    user_id: str
    query: str
    memory_types: Optional[List[str]] = None
    limit: int = Field(default=10, ge=1, le=100)
    min_relevance: float = Field(default=0.5, ge=0.0, le=1.0)


class MemoryResponse(BaseModel):
    """Response from Mem0 API"""

    memories: List[MemoryNode]
    total_count: int
    query_time_ms: float
