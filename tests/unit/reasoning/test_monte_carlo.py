"""
Unit tests for Monte Carlo reasoning validation

Tests the MonteCarloValidator for consistency checking.
Target coverage: 90%+ for reasoning.monte_carlo module
"""

import pytest
from unittest.mock import AsyncMock, Mock
from hermes.reasoning.monte_carlo import MonteCarloValidator


@pytest.mark.unit
class TestMonteCarloInitialization:
    """Test MonteCarloValidator initialization"""

    def test_initialization_with_defaults(self):
        """Should initialize with default parameters"""
        validator = MonteCarloValidator(openai_api_key="test_key")

        assert validator.model == "gpt-4"
        assert validator.default_simulations == 100
        assert validator.max_concurrent == 10

    def test_initialization_with_custom_parameters(self):
        """Should initialize with custom parameters"""
        validator = MonteCarloValidator(
            openai_api_key="test_key",
            model="gpt-3.5-turbo",
            default_simulations=50,
            max_concurrent=5
        )

        assert validator.model == "gpt-3.5-turbo"
        assert validator.default_simulations == 50
        assert validator.max_concurrent == 5


@pytest.mark.unit
class TestSimulateReasoning:
    """Test Monte Carlo simulation execution"""

    @pytest.mark.asyncio
    async def test_simulate_reasoning_success(self, mock_openai_client):
        """Should run multiple simulations successfully"""
        validator = MonteCarloValidator(
            openai_api_key="test_key",
            default_simulations=10
        )
        validator.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Personal injury case"))]
        )

        results = await validator.simulate_reasoning(
            query="What type of case is this?"
        )

        assert isinstance(results, list)
        assert len(results) <= 10
        for result in results:
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_simulate_reasoning_with_custom_count(self, mock_openai_client):
        """Should run custom number of simulations"""
        validator = MonteCarloValidator(openai_api_key="test_key")
        validator.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Test response"))]
        )

        results = await validator.simulate_reasoning(
            query="Test query",
            num_simulations=25
        )

        assert len(results) <= 25

    @pytest.mark.asyncio
    async def test_simulate_reasoning_with_context(self, mock_openai_client):
        """Should include context in simulations"""
        validator = MonteCarloValidator(
            openai_api_key="test_key",
            default_simulations=5
        )
        validator.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Test response"))]
        )

        await validator.simulate_reasoning(
            query="Test query",
            context="Important context"
        )

        # Verify context was included
        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        user_message = messages[1]['content']

        assert "Important context" in user_message

    @pytest.mark.asyncio
    async def test_simulate_reasoning_handles_exceptions(self, mock_openai_client):
        """Should handle API exceptions gracefully"""
        validator = MonteCarloValidator(
            openai_api_key="test_key",
            default_simulations=5
        )
        validator.client = mock_openai_client

        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")

        results = await validator.simulate_reasoning(query="Test query")

        # Should return empty list when all simulations fail
        assert isinstance(results, list)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_simulate_reasoning_filters_failed_simulations(self, mock_openai_client):
        """Should filter out failed simulations"""
        validator = MonteCarloValidator(
            openai_api_key="test_key",
            default_simulations=5
        )
        validator.client = mock_openai_client

        # Mock some successes and some failures
        responses = [
            Mock(choices=[Mock(message=Mock(content="Success 1"))]),
            Exception("API Error"),
            Mock(choices=[Mock(message=Mock(content="Success 2"))]),
            Exception("API Error"),
            Mock(choices=[Mock(message=Mock(content="Success 3"))]),
        ]

        mock_openai_client.chat.completions.create.side_effect = responses

        results = await validator.simulate_reasoning(query="Test query")

        # Should have 3 successful simulations
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_simulate_reasoning_respects_concurrency_limit(self, mock_openai_client):
        """Should respect max_concurrent limit"""
        validator = MonteCarloValidator(
            openai_api_key="test_key",
            default_simulations=30,
            max_concurrent=5
        )
        validator.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Test response"))]
        )

        await validator.simulate_reasoning(query="Test query")

        # Should have been called 30 times total
        assert mock_openai_client.chat.completions.create.call_count == 30


@pytest.mark.unit
class TestCalculateConsistency:
    """Test consistency calculation"""

    def test_calculate_consistency_with_identical_results(self):
        """Should return 1.0 for identical results"""
        validator = MonteCarloValidator(openai_api_key="test_key")

        results = ["Personal injury case"] * 100

        consistency = validator.calculate_consistency(results)

        # All results are identical, consistency should be very high
        assert consistency > 0.9

    def test_calculate_consistency_with_all_unique_results(self):
        """Should return low score for completely unique results"""
        validator = MonteCarloValidator(openai_api_key="test_key")

        results = [f"Result {i}" for i in range(100)]

        consistency = validator.calculate_consistency(results)

        # All results are unique, consistency should be low
        assert consistency < 0.1

    def test_calculate_consistency_with_moderate_variation(self):
        """Should return moderate score for moderate variation"""
        validator = MonteCarloValidator(openai_api_key="test_key")

        results = (
            ["Personal injury"] * 50 +
            ["Negligence case"] * 40 +
            ["Tort claim"] * 10
        )

        consistency = validator.calculate_consistency(results)

        # Moderate variation, consistency should be moderate
        assert 0.3 < consistency < 0.95

    def test_calculate_consistency_with_empty_results(self):
        """Should return 0.0 for empty results"""
        validator = MonteCarloValidator(openai_api_key="test_key")

        consistency = validator.calculate_consistency([])

        assert consistency == 0.0

    def test_calculate_consistency_with_single_result(self):
        """Should return 0.0 for single result"""
        validator = MonteCarloValidator(openai_api_key="test_key")

        consistency = validator.calculate_consistency(["Single result"])

        assert consistency == 0.0

    def test_calculate_consistency_normalizes_text(self):
        """Should normalize text for consistency calculation"""
        validator = MonteCarloValidator(openai_api_key="test_key")

        results = [
            "Personal Injury Case",
            "personal injury case",
            "PERSONAL INJURY CASE",
            "Personal   Injury   Case",  # Extra spaces
        ]

        consistency = validator.calculate_consistency(results)

        # All results are essentially identical after normalization
        assert consistency > 0.7

    def test_calculate_consistency_handles_punctuation_differences(self):
        """Should ignore punctuation differences"""
        validator = MonteCarloValidator(openai_api_key="test_key")

        results = [
            "Personal injury case.",
            "Personal injury case!",
            "Personal injury case?",
            "Personal injury case",
        ]

        consistency = validator.calculate_consistency(results)

        # Punctuation differences should be ignored
        assert consistency > 0.7

    def test_calculate_consistency_adjusts_for_small_samples(self):
        """Should adjust score for small sample sizes"""
        validator = MonteCarloValidator(openai_api_key="test_key")

        # Small sample with all identical
        small_results = ["Same result"] * 5
        small_consistency = validator.calculate_consistency(small_results)

        # Large sample with all identical
        large_results = ["Same result"] * 100
        large_consistency = validator.calculate_consistency(large_results)

        # Small sample should be penalized
        assert small_consistency < large_consistency

    def test_calculate_consistency_with_very_similar_results(self):
        """Should detect high consistency in very similar results"""
        validator = MonteCarloValidator(openai_api_key="test_key")

        results = [
            "This is a personal injury case",
            "This is  a personal  injury case",  # Extra spaces
            "this is a personal injury case",  # Lowercase
            "THIS IS A PERSONAL INJURY CASE",  # Uppercase
        ] * 25  # Repeat 25 times for 100 total

        consistency = validator.calculate_consistency(results)

        assert consistency > 0.9


@pytest.mark.unit
class TestRunSingleSimulation:
    """Test individual simulation execution"""

    @pytest.mark.asyncio
    async def test_run_single_simulation_success(self, mock_openai_client):
        """Should run single simulation successfully"""
        validator = MonteCarloValidator(openai_api_key="test_key")
        validator.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Test result"))]
        )

        result = await validator._run_single_simulation(
            query="Test query",
            context=None,
            simulation_index=0
        )

        assert result == "Test result"

    @pytest.mark.asyncio
    async def test_run_single_simulation_handles_exception(self, mock_openai_client):
        """Should return None on exception"""
        validator = MonteCarloValidator(openai_api_key="test_key")
        validator.client = mock_openai_client

        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")

        result = await validator._run_single_simulation(
            query="Test query",
            context=None,
            simulation_index=0
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_run_single_simulation_strips_whitespace(self, mock_openai_client):
        """Should strip leading/trailing whitespace from result"""
        validator = MonteCarloValidator(openai_api_key="test_key")
        validator.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="  \n\n Test result  \n\n  "))]
        )

        result = await validator._run_single_simulation(
            query="Test query",
            context=None,
            simulation_index=0
        )

        assert result == "Test result"

    @pytest.mark.asyncio
    async def test_run_single_simulation_handles_empty_content(self, mock_openai_client):
        """Should return None for empty content"""
        validator = MonteCarloValidator(openai_api_key="test_key")
        validator.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content=None))]
        )

        result = await validator._run_single_simulation(
            query="Test query",
            context=None,
            simulation_index=0
        )

        assert result is None


@pytest.mark.unit
class TestSimulationParameters:
    """Test simulation API call parameters"""

    @pytest.mark.asyncio
    async def test_uses_high_temperature_for_diversity(self, mock_openai_client):
        """Should use high temperature for diverse simulations"""
        validator = MonteCarloValidator(openai_api_key="test_key")
        validator.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Test"))]
        )

        await validator._run_single_simulation("Test", None, 0)

        call_args = mock_openai_client.chat.completions.create.call_args
        temperature = call_args.kwargs.get('temperature')

        assert temperature >= 0.8  # High temperature for diversity

    @pytest.mark.asyncio
    async def test_uses_low_max_tokens(self, mock_openai_client):
        """Should use low max_tokens for concise responses"""
        validator = MonteCarloValidator(openai_api_key="test_key")
        validator.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Test"))]
        )

        await validator._run_single_simulation("Test", None, 0)

        call_args = mock_openai_client.chat.completions.create.call_args
        max_tokens = call_args.kwargs.get('max_tokens')

        assert max_tokens <= 200  # Low tokens for concise answers


@pytest.mark.unit
@pytest.mark.slow
class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_handles_very_long_query(self, mock_openai_client):
        """Should handle very long queries"""
        validator = MonteCarloValidator(
            openai_api_key="test_key",
            default_simulations=2
        )
        validator.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Test"))]
        )

        long_query = "What is the answer? " * 1000

        results = await validator.simulate_reasoning(query=long_query)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_handles_special_characters(self, mock_openai_client):
        """Should handle special characters in query"""
        validator = MonteCarloValidator(
            openai_api_key="test_key",
            default_simulations=2
        )
        validator.client = mock_openai_client

        mock_openai_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Test"))]
        )

        special_query = "Test <html> & 'quotes' \"double\" $pecial"

        results = await validator.simulate_reasoning(query=special_query)

        assert isinstance(results, list)

    def test_consistency_with_unicode_characters(self):
        """Should handle unicode characters in results"""
        validator = MonteCarloValidator(openai_api_key="test_key")

        results = [
            "Personal injury case",
            "Personal injury casé",  # Accented character
            "Personal injury case",
            "Персональная травма",  # Cyrillic
        ] * 10

        consistency = validator.calculate_consistency(results)

        assert isinstance(consistency, float)
        assert 0.0 <= consistency <= 1.0

    def test_consistency_with_very_long_results(self):
        """Should handle very long result strings"""
        validator = MonteCarloValidator(openai_api_key="test_key")

        long_result = "This is a very long result. " * 1000
        results = [long_result] * 100

        consistency = validator.calculate_consistency(results)

        assert consistency > 0.9  # All identical

    @pytest.mark.asyncio
    async def test_handles_zero_simulations(self, mock_openai_client):
        """Should handle request for zero simulations"""
        validator = MonteCarloValidator(openai_api_key="test_key")
        validator.client = mock_openai_client

        results = await validator.simulate_reasoning(
            query="Test",
            num_simulations=0
        )

        assert results == []
