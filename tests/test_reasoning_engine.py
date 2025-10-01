"""
Test AI Reasoning Engine (ToT + Monte Carlo)
"""

import os
os.environ["OPENAI_API_KEY"] = "test-key-123"
os.environ["DEBUG"] = "true"

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from hermes.reasoning.tree_of_thought import TreeOfThoughtReasoner
from hermes.reasoning.monte_carlo import MonteCarloValidator
from hermes.reasoning.models import ReasoningPath, ReasoningResult, ValidationResult


class TestTreeOfThoughtReasoner:
    """Test Tree of Thought reasoning"""

    @pytest.mark.asyncio
    async def test_reasoner_initialization(self):
        """Test reasoner can be initialized"""
        reasoner = TreeOfThoughtReasoner(
            openai_api_key="test-key",
            num_paths=3
        )
        
        assert reasoner.num_paths == 3
        assert reasoner.model == "gpt-4"

    @pytest.mark.asyncio
    async def test_generate_reasoning_paths(self):
        """Test reasoning path generation"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test-key")
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """
1. First step
2. Second step
Conclusion: Test conclusion
"""
        
        with patch.object(reasoner.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            paths = await reasoner.generate_reasoning_paths(
                query="Test query",
                num_paths=2
            )
            
            assert len(paths) <= 2
            for path in paths:
                assert isinstance(path, ReasoningPath)
                assert path.query == "Test query"

    @pytest.mark.asyncio
    async def test_evaluate_paths(self):
        """Test path evaluation"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test-key")
        
        test_path = ReasoningPath(
            path_id="path_1",
            query="Test",
            reasoning_steps=["Step 1", "Step 2"],
            conclusion="Conclusion",
            confidence_score=0.8,
            evaluation_score=0.0,
        )
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "0.85"
        
        with patch.object(reasoner.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            evaluated = await reasoner.evaluate_paths([test_path])
            
            assert len(evaluated) == 1
            assert evaluated[0].evaluation_score > 0

    @pytest.mark.asyncio
    async def test_select_best_path(self):
        """Test best path selection"""
        reasoner = TreeOfThoughtReasoner(openai_api_key="test-key")
        
        paths = [
            ReasoningPath(
                path_id=f"path_{i}",
                query="Test",
                reasoning_steps=[],
                conclusion=f"Conclusion {i}",
                confidence_score=0.5 + i * 0.1,
                evaluation_score=0.6 + i * 0.1,
            )
            for i in range(3)
        ]
        
        best = await reasoner.select_best_path(paths)
        
        assert best.path_id == "path_2"  # Highest scores


class TestMonteCarloValidator:
    """Test Monte Carlo validation"""

    @pytest.mark.asyncio
    async def test_validator_initialization(self):
        """Test validator can be initialized"""
        validator = MonteCarloValidator(
            openai_api_key="test-key",
            default_simulations=10
        )
        
        assert validator.default_simulations == 10

    @pytest.mark.asyncio
    async def test_simulate_reasoning(self):
        """Test reasoning simulation"""
        validator = MonteCarloValidator(openai_api_key="test-key")
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Consistent answer"
        
        with patch.object(validator.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            results = await validator.simulate_reasoning(
                query="Test query",
                num_simulations=5
            )
            
            assert len(results) <= 5

    def test_calculate_consistency(self):
        """Test consistency calculation"""
        validator = MonteCarloValidator(openai_api_key="test-key")
        
        # All same results = high consistency
        results = ["Same answer"] * 10
        consistency = validator.calculate_consistency(results)
        assert consistency > 0.8
        
        # All different results = low consistency
        results = [f"Answer {i}" for i in range(10)]
        consistency = validator.calculate_consistency(results)
        assert consistency < 0.2

    def test_calculate_confidence(self):
        """Test confidence calculation"""
        validator = MonteCarloValidator(openai_api_key="test-key")
        
        confidence = validator.calculate_confidence(
            consistency_score=0.9,
            num_simulations=100
        )
        
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_validate(self):
        """Test full validation"""
        validator = MonteCarloValidator(openai_api_key="test-key")
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Consistent answer"
        
        with patch.object(validator.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await validator.validate(
                query="Test query",
                num_simulations=5
            )
            
            assert isinstance(result, ValidationResult)
            assert result.num_simulations <= 5
            assert 0.0 <= result.consistency_score <= 1.0
