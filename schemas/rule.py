from typing import Any

from pydantic import BaseModel, Field

from schemas.enums import DecisionType, RiskLevel


class Rule(BaseModel):
    rule_id: str
    name: str
    description: str = ""

    enabled: bool = True
    priority: int = Field(ge=0)

    action: str = "*"
    conditions: dict[str, Any] = Field(default_factory=dict)

    decision: DecisionType | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    weight: float | None = Field(default=None, ge=0.0)
    severity: RiskLevel
    reason: str
