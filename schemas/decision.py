from datetime import UTC, datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from schemas.enums import DecisionType, ExpertType


class Decision(BaseModel):

    """
    Final governance decision produced by SentinelAI
    after aggregating all expert evaluations.
    """

    decision_id: str = Field(
        ...,
        description="Unique identifier for the governance decision."
    )

    final_decision: DecisionType = Field(
        ...,
        description="Final decision after expert aggregation."
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="overall confidence of the final decision (0.0 - 1.0)."
    )

    expert_consulted: List[ExpertType] = Field(
        default_factory=list,
        description="List of experts consulted for this decision."
    )

    reasoning: str = Field(
        ...,
        description="Human-readable explanation of the final decision."
    )

    processing_time_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Time taken to process the request and reach a decision (in milliseconds)."
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata related to the decision-making process."
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the decision was created."
    )
