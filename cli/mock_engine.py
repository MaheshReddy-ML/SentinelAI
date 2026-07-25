"""Temporary engine adapter used exclusively by the terminal presentation layer.

Replace ``analyze_transaction`` with an integration adapter when the governance
engine is ready. This module intentionally performs no evaluation or routing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from schemas.request import FinancialRequest


@dataclass(frozen=True)
class ExpertResult:
    """A render-ready result supplied by a governance engine."""

    expert: str
    decision: str
    confidence: float
    execution_time_ms: float


@dataclass(frozen=True)
class AnalysisResult:
    """A render-ready governance report supplied by a governance engine."""

    final_decision: str
    confidence: float
    explanation: Sequence[str]
    expert_results: Sequence[ExpertResult]
    total_runtime_ms: float


def analyze_transaction(request: FinancialRequest) -> AnalysisResult:
    """Return deterministic demonstration data for the supplied request.

    The request is accepted to preserve the future engine integration boundary;
    this placeholder neither evaluates it nor reads governance rules.
    """
    del request
    expert_results = (
        ExpertResult("Policy Expert", "APPROVE", 0.98, 12.4),
        ExpertResult("Fraud Expert", "APPROVE", 0.96, 18.7),
        ExpertResult("Risk Expert", "REVIEW", 0.81, 15.2),
        ExpertResult("Compliance Expert", "APPROVE", 0.99, 11.8),
        ExpertResult("Spend Expert", "APPROVE", 0.93, 10.6),
    )
    return AnalysisResult(
        final_decision="REVIEW",
        confidence=0.93,
        explanation=(
            "The governance engine adapter returned a demonstration result.",
            "One expert requested a manual review before the transaction proceeds.",
            "Replace the mock adapter to connect a live governance engine.",
        ),
        expert_results=expert_results,
        total_runtime_ms=68.7,
    )
