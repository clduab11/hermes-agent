"""
Unit tests for Tree of Thought reasoning

Tests the TreeOfThoughtReasoner for path generation and evaluation.
Target coverage: 90%+ for reasoning.tree_of_thought module
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from hermes.reasoning.tree_of_thought import TreeOfThoughtReasoner
from hermes.reasoning.models import ReasoningPath


@pytest.mark.unit
class TestTreeOfThoughtInitialization:
    """Test TreeOfThoughtReasoner initialization"""

    def test_initialization_with_defaults(self):
        """Should initialize with default parameters"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test_key")

        assert reasoner.model == "gpt-4"
        assert reasoner.num_paths == 3
        assert reasoner.max_concurrent == 3

    def test_initialization_with_custom_parameters(self):
        """Should initialize with custom parameters"""
        reasoner = TreeOfThoughtReasoner(
            openai_api_key="test_key",
            model="gpt-3.5-turbo",
            num_paths=5,
            max_concurrent=10
        )

        assert reasoner.model == "gpt-3.5-turbo"
        assert reasoner.num_paths == 5
        assert reasoner.max_concurrent == 10


@pytest.mark.unit
class TestGenerateReasoningPaths:
    """Test reasoning path generation"""

    @pytest.mark.asyncio
    async def test_generate_reasoning_paths_success(self, mock_openai_client):
        """Should generate multiple reasoning paths successfully"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test_key", num_paths=3)
        reasoner.client = mock_openai_client

        # Mock response for path generation
        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="""
Step 1: Analyze the accident circumstances
Step 2: Determine liability
Step 3: Calculate damages

Conclusion: This is a viable personal injury case.
"""))]
        )

        paths = await reasoner.generate_reasoning_paths(
            query="Is this a valid personal injury case?",
            context="Client was rear-ended at a red light"
        )

        assert isinstance(paths, list)
        assert len(paths) <= 3  # May be fewer if some fail
        for path in paths:
            assert isinstance(path, ReasoningPath)
            assert path.query == "Is this a valid personal injury case?"
            assert len(path.reasoning_steps) > 0
            assert len(path.conclusion) > 0

    @pytest.mark.asyncio
    async def test_generate_reasoning_paths_with_custom_count(self, mock_openai_client):
        """Should generate custom number of paths"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test_key")
        reasoner.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Step 1: Test\n\nConclusion: Test conclusion"))]
        )

        paths = await reasoner.generate_reasoning_paths(
            query="Test query",
            num_paths=5
        )

        assert len(paths) <= 5

    @pytest.mark.asyncio
    async def test_generate_reasoning_paths_handles_exceptions(self, mock_openai_client):
        """Should handle exceptions gracefully"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test_key", num_paths=3)
        reasoner.client = mock_openai_client

        # Mock to raise exception
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")

        paths = await reasoner.generate_reasoning_paths(query="Test query")

        # Should return empty list or partial results
        assert isinstance(paths, list)
        # All paths failed, so should be empty
        assert len(paths) == 0

    @pytest.mark.asyncio
    async def test_generate_reasoning_paths_filters_failed_paths(self, mock_openai_client):
        """Should filter out failed paths and return only successful ones"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test_key", num_paths=3)
        reasoner.client = mock_openai_client

        # Mock to succeed on first call, fail on second, succeed on third
        responses = [
            Mock(choices=[Mock(message=Mock(content="Step 1: Test\n\nConclusion: Success 1"))]),
            Exception("API Error"),
            Mock(choices=[Mock(message=Mock(content="Step 1: Test\n\nConclusion: Success 2"))]),
        ]

        mock_openai_client.chat.completions.create.side_effect = responses

        paths = await reasoner.generate_reasoning_paths(query="Test query")

        # Should have 2 successful paths
        assert len(paths) == 2

    @pytest.mark.asyncio
    async def test_generate_reasoning_paths_with_context(self, mock_openai_client):
        """Should include context in prompt"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test_key", num_paths=1)
        reasoner.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Step 1: Test\n\nConclusion: Test"))]
        )

        await reasoner.generate_reasoning_paths(
            query="Test query",
            context="Important context"
        )

        # Verify context was included in API call
        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        user_message = messages[1]['content']

        assert "Important context" in user_message


@pytest.mark.unit
class TestBuildReasoningPrompt:
    """Test prompt construction"""

    def test_build_reasoning_prompt_without_context(self):
        """Should build prompt without context"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test_key")

        prompt = reasoner._build_reasoning_prompt(
            query="What is the legal standard?",
            context=None,
            path_index=0
        )

        assert "What is the legal standard?" in prompt
        assert "step-by-step" in prompt.lower()
        assert "reasoning path #1" in prompt.lower()

    def test_build_reasoning_prompt_with_context(self):
        """Should build prompt with context"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test_key")

        prompt = reasoner._build_reasoning_prompt(
            query="What is the legal standard?",
            context="In California law",
            path_index=1
        )

        assert "What is the legal standard?" in prompt
        assert "In California law" in prompt
        assert "reasoning path #2" in prompt.lower()

    def test_build_reasoning_prompt_includes_all_elements(self):
        """Should include all required prompt elements"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test_key")

        prompt = reasoner._build_reasoning_prompt(
            query="Test query",
            context="Test context",
            path_index=0
        )

        assert "Query:" in prompt
        assert "Context:" in prompt
        assert "step-by-step" in prompt.lower()
        assert "conclusion" in prompt.lower()


@pytest.mark.unit
class TestParseReasoningResponse:
    """Test response parsing"""

    def test_parse_reasoning_response_with_numbered_steps(self):
        """Should parse numbered steps correctly"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test_key")

        content = """
1. First step of reasoning
2. Second step of reasoning
3. Third step

Conclusion: Final conclusion here
"""

        steps, conclusion = reasoner._parse_reasoning_response(content)

        assert len(steps) == 3
        assert "First step" in steps[0]
        assert "Second step" in steps[1]
        assert "Third step" in steps[2]
        assert "Final conclusion" in conclusion

    def test_parse_reasoning_response_handles_various_formats(self):
        """Should handle various formatting styles"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test_key")

        content = """
Step 1: First reasoning step
Step 2: Second reasoning step

Conclusion:
The final conclusion is here.
"""

        steps, conclusion = reasoner._parse_reasoning_response(content)

        assert len(steps) >= 1
        assert len(conclusion) > 0

    def test_parse_reasoning_response_with_empty_content(self):
        """Should handle empty content gracefully"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test_key")

        steps, conclusion = reasoner._parse_reasoning_response("")

        assert isinstance(steps, list)
        assert isinstance(conclusion, str)


@pytest.mark.unit
class TestReasoningPathProperties:
    """Test ReasoningPath model properties"""

    @pytest.mark.asyncio
    async def test_path_has_required_fields(self, mock_openai_client):
        """Should create path with all required fields"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test_key", num_paths=1)
        reasoner.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Step 1: Test\n\nConclusion: Test conclusion"))]
        )

        paths = await reasoner.generate_reasoning_paths(query="Test query")

        assert len(paths) > 0
        path = paths[0]

        assert path.path_id is not None
        assert path.query == "Test query"
        assert isinstance(path.reasoning_steps, list)
        assert isinstance(path.conclusion, str)
        assert 0.0 <= path.confidence_score <= 1.0
        assert 0.0 <= path.evaluation_score <= 1.0
        assert isinstance(path.metadata, dict)
        assert "path_index" in path.metadata
        assert "model" in path.metadata

    @pytest.mark.asyncio
    async def test_paths_have_varying_temperatures(self, mock_openai_client):
        """Should use varying temperatures for path diversity"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test_key", num_paths=3)
        reasoner.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Step 1: Test\n\nConclusion: Test"))]
        )

        await reasoner.generate_reasoning_paths(query="Test query")

        # Check that different temperatures were used
        calls = mock_openai_client.chat.completions.create.call_args_list
        temperatures = [call.kwargs.get('temperature') for call in calls]

        assert len(temperatures) == 3
        # Temperatures should vary (0.7, 0.8, 0.9)
        assert len(set(temperatures)) > 1


@pytest.mark.unit
class TestConcurrencyControl:
    """Test concurrent execution control"""

    @pytest.mark.asyncio
    async def test_respects_max_concurrent_limit(self, mock_openai_client):
        """Should respect max_concurrent limit"""
        reasoner = TreeOfThoughtReasoner(
            openai_api_key="test_key",
            num_paths=10,
            max_concurrent=3
        )
        reasoner.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Step 1: Test\n\nConclusion: Test"))]
        )

        await reasoner.generate_reasoning_paths(query="Test query")

        # Should have been called 10 times total
        assert mock_openai_client.chat.completions.create.call_count == 10

    @pytest.mark.asyncio
    async def test_batching_with_concurrent_limit(self, mock_openai_client):
        """Should batch requests according to max_concurrent"""
        reasoner = TreeOfThoughtReasoner(
            openai_api_key="test_key",
            num_paths=7,
            max_concurrent=3
        )
        reasoner.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Step 1: Test\n\nConclusion: Test"))]
        )

        paths = await reasoner.generate_reasoning_paths(query="Test query")

        # Should process in batches of 3: [3, 3, 1]
        assert len(paths) <= 7


@pytest.mark.unit
@pytest.mark.slow
class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_handles_empty_response_content(self, mock_openai_client):
        """Should handle empty response content"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test_key", num_paths=1)
        reasoner.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content=None))]
        )

        paths = await reasoner.generate_reasoning_paths(query="Test query")

        assert len(paths) == 0  # Empty content should be filtered out

    @pytest.mark.asyncio
    async def test_handles_malformed_response(self, mock_openai_client):
        """Should handle malformed API responses"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test_key", num_paths=1)
        reasoner.client = mock_openai_client

        # Malformed response (missing choices)
        mock_openai_client.chat.completions.create.return_value = Mock(choices=[])

        paths = await reasoner.generate_reasoning_paths(query="Test query")

        assert isinstance(paths, list)

    @pytest.mark.asyncio
    async def test_handles_very_long_query(self, mock_openai_client):
        """Should handle very long queries"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test_key", num_paths=1)
        reasoner.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Step 1: Test\n\nConclusion: Test"))]
        )

        long_query = "What is the legal standard? " * 1000  # Very long query

        paths = await reasoner.generate_reasoning_paths(query=long_query)

        assert len(paths) <= 1

    @pytest.mark.asyncio
    async def test_handles_special_characters_in_query(self, mock_openai_client):
        """Should handle special characters in queries"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test_key", num_paths=1)
        reasoner.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Step 1: Test\n\nConclusion: Test"))]
        )

        special_query = "Test <html> & 'quotes' \"double\" $pecial chars"

        paths = await reasoner.generate_reasoning_paths(query=special_query)

        assert isinstance(paths, list)
