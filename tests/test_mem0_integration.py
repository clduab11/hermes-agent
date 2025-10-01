"""
Test Mem0 integration
"""

import os
os.environ["OPENAI_API_KEY"] = "test-key-123"
os.environ["DEBUG"] = "true"

import pytest
from unittest.mock import AsyncMock, Mock, patch
from decimal import Decimal

from hermes.integrations.mem0.client import Mem0Client
from hermes.integrations.mem0.models import MemoryNode, MemoryQuery, MemoryResponse


class TestMem0Client:
    """Test Mem0 API client"""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client can be initialized"""
        client = Mem0Client(api_key="test-key")
        await client.initialize()
        
        assert client._client is not None
        await client.close()

    @pytest.mark.asyncio
    async def test_create_memory(self):
        """Test memory creation"""
        client = Mem0Client(api_key="test-key")
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "id": "mem_123",
                "user_id": "user_1",
                "content": "Test memory",
                "memory_type": "fact",
                "metadata": {},
                "relevance_score": 1.0,
            }
            
            memory = await client.create_memory(
                user_id="user_1",
                content="Test memory",
                memory_type="fact"
            )
            
            assert memory.id == "mem_123"
            assert memory.user_id == "user_1"
            assert memory.content == "Test memory"
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_memories(self):
        """Test memory search"""
        client = Mem0Client(api_key="test-key")
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "memories": [
                    {
                        "id": "mem_1",
                        "user_id": "user_1",
                        "content": "Memory 1",
                        "memory_type": "fact",
                        "metadata": {},
                        "relevance_score": 0.9,
                    }
                ],
                "total_count": 1,
                "query_time_ms": 50.0,
            }
            
            response = await client.search_memories(
                user_id="user_1",
                query="test query"
            )
            
            assert isinstance(response, MemoryResponse)
            assert len(response.memories) == 1
            assert response.total_count == 1

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager"""
        async with Mem0Client(api_key="test-key") as client:
            assert client._client is not None
        
        # Should be closed after exiting context
        assert client._client is None


class TestMemoryModels:
    """Test Mem0 data models"""

    def test_memory_node_validation(self):
        """Test MemoryNode validation"""
        node = MemoryNode(
            user_id="user_1",
            memory_type="fact",
            content="Test content",
        )
        
        assert node.user_id == "user_1"
        assert node.relevance_score == 1.0  # Default value

    def test_memory_query_validation(self):
        """Test MemoryQuery validation"""
        query = MemoryQuery(
            user_id="user_1",
            query="test",
            limit=5
        )
        
        assert query.limit == 5
        assert query.min_relevance == 0.5  # Default value
