"""
Data models for AI reasoning engine
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReasoningPath(BaseModel):
    """A single reasoning path in Tree of Thought"""

    path_id: str
    query: str
    reasoning_steps: List[str]
    conclusion: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    evaluation_score: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReasoningResult(BaseModel):
    """Result from Tree of Thought reasoning"""

    query: str
    paths: List[ReasoningPath]
    selected_path: ReasoningPath
    total_paths_generated: int
    selection_method: str
    processing_time_ms: float


class ValidationResult(BaseModel):
    """Result from Monte Carlo validation"""

    query: str
    num_simulations: int
    consistency_score: float = Field(ge=0.0, le=1.0)
    confidence_level: float = Field(ge=0.0, le=1.0)
    validated: bool
    reasoning_variance: float
    execution_time_ms: float
    simulation_results: List[str]
