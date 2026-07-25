from typing import Any

from pydantic import BaseModel

from schemas.enums import DecisionType, RiskLevel


class Rule(BaseModel):
    rule_id: str
    name: str
    description: str

    enabled: bool = True
    priority: int

    action: str
    conditions: dict[str, Any]

    decision: DecisionType
    confidence: float
    severity: RiskLevel
    reason: str