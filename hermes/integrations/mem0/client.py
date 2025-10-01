"""
Mem0 API Client - Production-ready implementation
Follows September 2025 async/await best practices
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

from .models import MemoryNode, MemoryResponse

logger = logging.getLogger(__name__)


class Mem0Client:
    """
    Mem0 API client for knowledge graph operations.
    
    Implements async/await patterns, connection pooling, and retry logic
    following September 2025 best practices.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.mem0.ai/v1",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def initialize(self) -> None:
        """Initialize HTTP client with connection pooling"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            )
            logger.info("Mem0 client initialized")

    async def close(self) -> None:
        """Close HTTP client and cleanup resources"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("Mem0 client closed")

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.
        
        Implements exponential backoff for transient failures.
        """
        if not self._client:
            await self.initialize()

        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = await self._client.request(method, endpoint, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    # Server error - retry with backoff
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"Mem0 API error {e.response.status_code}, "
                        f"retry {attempt + 1}/{self.max_retries} in {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                    last_exception = e
                else:
                    # Client error - don't retry
                    logger.error(f"Mem0 API client error: {e.response.text}")
                    raise
            except httpx.RequestError as e:
                # Network error - retry
                wait_time = 2 ** attempt
                logger.warning(
                    f"Mem0 network error: {e}, "
                    f"retry {attempt + 1}/{self.max_retries} in {wait_time}s"
                )
                await asyncio.sleep(wait_time)
                last_exception = e

        raise Exception(f"Mem0 API request failed after {self.max_retries} retries") from last_exception

    async def create_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str = "fact",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryNode:
        """
        Create a new memory node.
        
        Args:
            user_id: User or session identifier
            content: Memory content
            memory_type: Type of memory (fact, event, preference)
            metadata: Additional metadata
            
        Returns:
            Created memory node
        """
        payload = {
            "user_id": user_id,
            "content": content,
            "memory_type": memory_type,
            "metadata": metadata or {},
        }

        response = await self._request("POST", "/memories", json=payload)
        return MemoryNode(**response)

    async def get_memory(self, memory_id: str) -> MemoryNode:
        """
        Retrieve a specific memory by ID.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory node
        """
        response = await self._request("GET", f"/memories/{memory_id}")
        return MemoryNode(**response)

    async def search_memories(
        self,
        user_id: str,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 10,
        min_relevance: float = 0.5,
    ) -> MemoryResponse:
        """
        Search memories using semantic search.
        
        Args:
            user_id: User identifier to search within
            query: Search query
            memory_types: Filter by memory types
            limit: Maximum results to return
            min_relevance: Minimum relevance score
            
        Returns:
            Memory search response
        """
        params = {
            "user_id": user_id,
            "query": query,
            "limit": limit,
            "min_relevance": min_relevance,
        }
        if memory_types:
            params["memory_types"] = ",".join(memory_types)

        response = await self._request("GET", "/memories/search", params=params)
        
        memories = [MemoryNode(**m) for m in response.get("memories", [])]
        return MemoryResponse(
            memories=memories,
            total_count=response.get("total_count", len(memories)),
            query_time_ms=response.get("query_time_ms", 0),
        )

    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryNode:
        """
        Update an existing memory.
        
        Args:
            memory_id: Memory identifier
            content: New content (optional)
            metadata: New metadata (optional)
            
        Returns:
            Updated memory node
        """
        payload = {}
        if content is not None:
            payload["content"] = content
        if metadata is not None:
            payload["metadata"] = metadata

        response = await self._request("PATCH", f"/memories/{memory_id}", json=payload)
        return MemoryNode(**response)

    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if successful
        """
        await self._request("DELETE", f"/memories/{memory_id}")
        return True

    async def get_user_memories(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[MemoryNode]:
        """
        Get all memories for a user.
        
        Args:
            user_id: User identifier
            memory_type: Filter by memory type (optional)
            limit: Maximum results
            
        Returns:
            List of memory nodes
        """
        params = {"user_id": user_id, "limit": limit}
        if memory_type:
            params["memory_type"] = memory_type

        response = await self._request("GET", "/memories", params=params)
        return [MemoryNode(**m) for m in response.get("memories", [])]
