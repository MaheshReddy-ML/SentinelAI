from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from schemas.enums import RiskLevel
from schemas.rule import Rule


@dataclass(slots=True)
class RiskAssessment:
    score: float
    confidence: float
    risk_level: RiskLevel
    reasoning: list[str]
    metadata: dict[str, Any]


class RiskEngine:
    """
    Converts matched risk rules into a normalized risk assessment.
    """

    MAX_SCORE = 100.0

    @classmethod
    def assess(
        cls,
        matched_rules: list[Rule],
    ) -> RiskAssessment:

        if not matched_rules:
            return RiskAssessment(
                score=0.0,
                confidence=0.0,
                risk_level=RiskLevel.LOW,
                reasoning=[],
                metadata={"matched_rules": 0},
            )

        score = min(
            sum(rule.weight or 0.0 for rule in matched_rules),
            cls.MAX_SCORE,
        )

        confidence = max(
            rule.confidence or 0.0
            for rule in matched_rules
        )

        reasoning = [
            rule.reason
            for rule in matched_rules
        ]

        metadata = {
            "matched_rules": len(matched_rules),
            "rule_ids": [
                rule.rule_id
                for rule in matched_rules
            ],
        }

        return RiskAssessment(
            score=score,
            confidence=confidence,
            risk_level=cls._risk_level(score),
            reasoning=reasoning,
            metadata=metadata,
        )

    @staticmethod
    def _risk_level(
        score: float,
    ) -> RiskLevel:

        if score >= 85:
            return RiskLevel.CRITICAL

        if score >= 60:
            return RiskLevel.HIGH

        if score >= 30:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW
