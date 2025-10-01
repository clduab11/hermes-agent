"""
Tree of Thought Reasoning Implementation
Following September 2025 best practices for async AI reasoning
"""

import asyncio
import logging
import time
from typing import List, Optional
from uuid import uuid4

import openai

from .models import ReasoningPath, ReasoningResult

logger = logging.getLogger(__name__)


class TreeOfThoughtReasoner:
    """
    Implements Tree of Thought reasoning for enhanced AI decision quality.
    
    Generates multiple reasoning paths, evaluates each, and selects the best one.
    Designed to reduce hallucinations and improve response quality.
    """

    def __init__(
        self,
        openai_api_key: str,
        model: str = "gpt-4",
        num_paths: int = 3,
        max_concurrent: int = 3,
    ):
        self.client = openai.AsyncOpenAI(api_key=openai_api_key)
        self.model = model
        self.num_paths = num_paths
        self.max_concurrent = max_concurrent

    async def generate_reasoning_paths(
        self,
        query: str,
        context: Optional[str] = None,
        num_paths: Optional[int] = None,
    ) -> List[ReasoningPath]:
        """
        Generate multiple reasoning paths for a query.
        
        Args:
            query: The question or problem to reason about
            context: Optional context information
            num_paths: Number of paths to generate (defaults to self.num_paths)
            
        Returns:
            List of reasoning paths
        """
        num_paths = num_paths or self.num_paths
        
        # Create tasks for concurrent path generation
        tasks = [
            self._generate_single_path(query, context, i)
            for i in range(num_paths)
        ]
        
        # Execute concurrently with limit
        paths = []
        for i in range(0, len(tasks), self.max_concurrent):
            batch = tasks[i:i + self.max_concurrent]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Path generation failed: {result}")
                elif result:
                    paths.append(result)
        
        logger.info(f"Generated {len(paths)} reasoning paths for query")
        return paths

    async def _generate_single_path(
        self,
        query: str,
        context: Optional[str],
        path_index: int,
    ) -> Optional[ReasoningPath]:
        """Generate a single reasoning path"""
        try:
            prompt = self._build_reasoning_prompt(query, context, path_index)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert legal reasoning assistant. Think step by step and provide clear, logical reasoning."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7 + (path_index * 0.1),  # Vary temperature for diversity
                max_tokens=1000,
            )
            
            content = response.choices[0].message.content
            if not content:
                return None
            
            # Parse response into reasoning steps
            steps, conclusion = self._parse_reasoning_response(content)
            
            return ReasoningPath(
                path_id=str(uuid4()),
                query=query,
                reasoning_steps=steps,
                conclusion=conclusion,
                confidence_score=0.8,  # Will be refined by evaluation
                evaluation_score=0.0,  # Set during evaluation
                metadata={"path_index": path_index, "model": self.model},
            )
            
        except Exception as e:
            logger.error(f"Failed to generate reasoning path {path_index}: {e}")
            return None

    def _build_reasoning_prompt(
        self,
        query: str,
        context: Optional[str],
        path_index: int,
    ) -> str:
        """Build prompt for reasoning path generation"""
        prompt = f"""Analyze the following query using step-by-step reasoning:

Query: {query}
"""
        if context:
            prompt += f"\nContext: {context}\n"
        
        prompt += """
Please provide:
1. Step-by-step reasoning (number each step)
2. A clear conclusion

Think carefully and consider multiple angles. This is reasoning path #{path_index + 1}.
"""
        return prompt

    def _parse_reasoning_response(self, content: str) -> tuple[List[str], str]:
        """Parse LLM response into steps and conclusion"""
        lines = content.strip().split('\n')
        steps = []
        conclusion = ""
        
        in_conclusion = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect conclusion section
            if any(marker in line.lower() for marker in ['conclusion:', 'therefore:', 'in summary:']):
                in_conclusion = True
                if ':' in line:
                    conclusion = line.split(':', 1)[1].strip()
                continue
            
            if in_conclusion:
                conclusion += " " + line
            else:
                # Extract numbered steps
                if line[0].isdigit() or line.startswith('-') or line.startswith('•'):
                    steps.append(line)
        
        if not conclusion and steps:
            # Use last step as conclusion if not explicitly marked
            conclusion = steps[-1]
        
        return steps, conclusion.strip()

    async def evaluate_paths(self, paths: List[ReasoningPath]) -> List[ReasoningPath]:
        """
        Evaluate reasoning paths to score their quality.
        
        Args:
            paths: List of reasoning paths to evaluate
            
        Returns:
            Paths with updated evaluation scores
        """
        evaluation_tasks = [self._evaluate_single_path(path) for path in paths]
        evaluated = await asyncio.gather(*evaluation_tasks, return_exceptions=True)
        
        result_paths = []
        for result in evaluated:
            if isinstance(result, Exception):
                logger.error(f"Path evaluation failed: {result}")
            elif result:
                result_paths.append(result)
        
        return result_paths

    async def _evaluate_single_path(self, path: ReasoningPath) -> ReasoningPath:
        """Evaluate a single reasoning path"""
        try:
            prompt = f"""Evaluate the quality of this reasoning:

Query: {path.query}

Reasoning Steps:
{chr(10).join(path.reasoning_steps)}

Conclusion: {path.conclusion}

Rate this reasoning on a scale of 0.0 to 1.0 based on:
- Logical consistency
- Relevance to the query
- Completeness
- Clarity

Provide only a number between 0.0 and 1.0.
"""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at evaluating logical reasoning. Provide only a numerical score."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=10,
            )
            
            content = response.choices[0].message.content
            if content:
                # Extract number from response
                score = float(''.join(c for c in content if c.isdigit() or c == '.'))
                score = max(0.0, min(1.0, score))
                path.evaluation_score = score
            
        except Exception as e:
            logger.error(f"Failed to evaluate path: {e}")
            path.evaluation_score = 0.5  # Default middle score
        
        return path

    async def select_best_path(
        self,
        paths: List[ReasoningPath],
        evaluation_weight: float = 0.7,
        confidence_weight: float = 0.3,
    ) -> ReasoningPath:
        """
        Select the best reasoning path based on evaluation and confidence.
        
        Args:
            paths: List of evaluated paths
            evaluation_weight: Weight for evaluation score
            confidence_weight: Weight for confidence score
            
        Returns:
            Best reasoning path
        """
        if not paths:
            raise ValueError("No paths provided for selection")
        
        # Calculate combined score
        for path in paths:
            path.metadata["combined_score"] = (
                path.evaluation_score * evaluation_weight +
                path.confidence_score * confidence_weight
            )
        
        # Sort by combined score
        sorted_paths = sorted(
            paths,
            key=lambda p: p.metadata.get("combined_score", 0),
            reverse=True
        )
        
        best_path = sorted_paths[0]
        logger.info(f"Selected best path with score: {best_path.metadata['combined_score']:.3f}")
        
        return best_path

    async def reason(
        self,
        query: str,
        context: Optional[str] = None,
    ) -> ReasoningResult:
        """
        Execute full Tree of Thought reasoning.
        
        Args:
            query: The question or problem to reason about
            context: Optional context information
            
        Returns:
            Complete reasoning result with selected best path
        """
        start_time = time.time()
        
        # Generate multiple reasoning paths
        paths = await self.generate_reasoning_paths(query, context)
        
        if not paths:
            raise ValueError("Failed to generate any reasoning paths")
        
        # Evaluate all paths
        evaluated_paths = await self.evaluate_paths(paths)
        
        # Select best path
        best_path = await self.select_best_path(evaluated_paths)
        
        processing_time = (time.time() - start_time) * 1000
        
        return ReasoningResult(
            query=query,
            paths=evaluated_paths,
            selected_path=best_path,
            total_paths_generated=len(paths),
            selection_method="weighted_score",
            processing_time_ms=processing_time,
        )
