"""
Monte Carlo Simulation for Reasoning Validation
Following September 2025 best practices
"""

import asyncio
import logging
import statistics
import time
from typing import List, Optional

import openai

from .models import ValidationResult

logger = logging.getLogger(__name__)


class MonteCarloValidator:
    """
    Monte Carlo simulation validator for reasoning consistency.
    
    Runs multiple independent reasoning attempts and validates consistency
    to detect hallucinations and increase confidence in AI responses.
    """

    def __init__(
        self,
        openai_api_key: str,
        model: str = "gpt-4",
        default_simulations: int = 100,
        max_concurrent: int = 10,
    ):
        self.client = openai.AsyncOpenAI(api_key=openai_api_key)
        self.model = model
        self.default_simulations = default_simulations
        self.max_concurrent = max_concurrent

    async def simulate_reasoning(
        self,
        query: str,
        context: Optional[str] = None,
        num_simulations: Optional[int] = None,
    ) -> List[str]:
        """
        Run Monte Carlo simulations for a query.
        
        Args:
            query: The question or problem
            context: Optional context
            num_simulations: Number of simulations (default: self.default_simulations)
            
        Returns:
            List of reasoning conclusions from simulations
        """
        num_simulations = num_simulations or self.default_simulations
        
        # Create simulation tasks
        tasks = [
            self._run_single_simulation(query, context, i)
            for i in range(num_simulations)
        ]
        
        # Execute in batches to control concurrency
        results = []
        for i in range(0, len(tasks), self.max_concurrent):
            batch = tasks[i:i + self.max_concurrent]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.warning(f"Simulation failed: {result}")
                elif result:
                    results.append(result)
        
        logger.info(f"Completed {len(results)}/{num_simulations} Monte Carlo simulations")
        return results

    async def _run_single_simulation(
        self,
        query: str,
        context: Optional[str],
        simulation_index: int,
    ) -> Optional[str]:
        """Run a single Monte Carlo simulation"""
        try:
            prompt = f"""Answer the following question concisely:

Query: {query}
"""
            if context:
                prompt += f"\nContext: {context}\n"
            
            prompt += "\nProvide a brief, direct answer."
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a concise expert assistant. Provide brief, accurate answers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,  # Higher temperature for diversity
                max_tokens=200,
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else None
            
        except Exception as e:
            logger.error(f"Simulation {simulation_index} failed: {e}")
            return None

    def calculate_consistency(self, results: List[str]) -> float:
        """
        Calculate consistency score from simulation results.
        
        Uses semantic similarity and variance analysis.
        
        Args:
            results: List of simulation results
            
        Returns:
            Consistency score (0.0 to 1.0)
        """
        if not results or len(results) < 2:
            return 0.0
        
        # Simple consistency metric: check for common patterns
        # In production, use embeddings for semantic similarity
        
        # Count unique responses (normalized)
        unique_normalized = set()
        for result in results:
            # Normalize by converting to lowercase and removing punctuation
            normalized = ''.join(c.lower() for c in result if c.isalnum() or c.isspace())
            normalized = ' '.join(normalized.split())  # Normalize whitespace
            unique_normalized.add(normalized)
        
        # Consistency = 1 - (unique_responses / total_responses)
        # If all responses are identical, consistency = 1.0
        # If all responses are unique, consistency = 0.0
        uniqueness_ratio = len(unique_normalized) / len(results)
        consistency = max(0.0, 1.0 - uniqueness_ratio)
        
        # Adjust for small sample sizes
        if len(results) < 10:
            consistency *= (len(results) / 10)
        
        return consistency

    def calculate_confidence(
        self,
        consistency_score: float,
        num_simulations: int,
    ) -> float:
        """
        Calculate confidence level based on consistency and sample size.
        
        Args:
            consistency_score: Consistency score from simulations
            num_simulations: Number of simulations performed
            
        Returns:
            Confidence level (0.0 to 1.0)
        """
        # Base confidence from consistency
        confidence = consistency_score
        
        # Adjust for sample size (more samples = higher confidence)
        sample_size_factor = min(1.0, num_simulations / 100)
        confidence *= (0.7 + 0.3 * sample_size_factor)
        
        return min(1.0, confidence)

    def calculate_variance(self, results: List[str]) -> float:
        """
        Calculate reasoning variance from results.
        
        Args:
            results: List of simulation results
            
        Returns:
            Variance metric (0.0 = no variance, 1.0 = high variance)
        """
        if not results or len(results) < 2:
            return 0.0
        
        # Calculate length variance as a simple metric
        lengths = [len(result) for result in results]
        
        if len(lengths) < 2:
            return 0.0
        
        try:
            mean_length = statistics.mean(lengths)
            std_dev = statistics.stdev(lengths)
            
            # Coefficient of variation (normalized variance)
            if mean_length > 0:
                cv = std_dev / mean_length
                # Cap at 1.0
                return min(1.0, cv)
            else:
                return 0.0
        except Exception:
            return 0.0

    async def validate(
        self,
        query: str,
        context: Optional[str] = None,
        num_simulations: Optional[int] = None,
        min_consistency: float = 0.7,
    ) -> ValidationResult:
        """
        Validate reasoning using Monte Carlo simulation.
        
        Args:
            query: The question or problem
            context: Optional context
            num_simulations: Number of simulations
            min_consistency: Minimum consistency threshold for validation
            
        Returns:
            Validation result with consistency and confidence scores
        """
        start_time = time.time()
        num_simulations = num_simulations or self.default_simulations
        
        # Run simulations
        results = await self.simulate_reasoning(query, context, num_simulations)
        
        if not results:
            return ValidationResult(
                query=query,
                num_simulations=0,
                consistency_score=0.0,
                confidence_level=0.0,
                validated=False,
                reasoning_variance=1.0,
                execution_time_ms=0,
                simulation_results=[],
            )
        
        # Calculate metrics
        consistency = self.calculate_consistency(results)
        confidence = self.calculate_confidence(consistency, len(results))
        variance = self.calculate_variance(results)
        validated = consistency >= min_consistency
        
        execution_time = (time.time() - start_time) * 1000
        
        logger.info(
            f"Monte Carlo validation: consistency={consistency:.3f}, "
            f"confidence={confidence:.3f}, validated={validated}"
        )
        
        return ValidationResult(
            query=query,
            num_simulations=len(results),
            consistency_score=consistency,
            confidence_level=confidence,
            validated=validated,
            reasoning_variance=variance,
            execution_time_ms=execution_time,
            simulation_results=results[:10],  # Store first 10 for inspection
        )
