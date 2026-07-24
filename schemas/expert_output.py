from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from schemas.enums import (
    DecisionType,
    ExpertType,
    PolicyResult,
    RiskLevel,
)


class ExpertOutput(BaseModel):
    """
    Standard output returned by every governance expert.
    """

    expert: ExpertType = Field(
        ...,
        description="Expert that generated this output."
    )

    decision: DecisionType = Field(
        ...,
        description="Expert's recommendation for the request."
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score of the expert's decision (0.0 - 1.0)."
    )

    score: float = Field(
        default=0.0,
        ge=0.0,
        description="Expert-specific numerical score."
    )

    risk_level: Optional[RiskLevel] = Field(
        default=None,
        description="Risk level assigned by the expert, if applicable."
    )

    policy_result: Optional[PolicyResult] = Field(
        default=None,
        description="Policy evaluation result, if applicable."
    )

    reasoning: str = Field(
        ...,
        description="Human-readable explanation of the expert's decision."
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Expert-specific metadata or additional evaluation details."
    )

    evaluated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the expert completed the evaluation."
    )