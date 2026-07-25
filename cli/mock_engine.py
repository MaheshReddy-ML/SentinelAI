"""Adapter from the terminal presentation layer to the rule-driven engine."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
from time import perf_counter
from typing import Sequence

from models.experts.compliance_expert import ComplianceExpert
from models.experts.audit_expert import AuditExpert
from models.experts.fraud_expert import FraudExpert
from models.experts.policy_expert import PolicyExpert
from models.experts.risk_expert import RiskExpert
from models.experts.spend_expert import SpendExpert
from schemas.enums import DecisionType
from schemas.request import FinancialRequest


@dataclass(frozen=True)
class ExpertResult:
    """A render-ready result supplied by a governance engine."""

    expert: str
    decision: str
    confidence: float | None
    execution_time_ms: float
    metadata: dict[str, object]


@dataclass(frozen=True)
class AnalysisResult:
    """A render-ready governance report supplied by a governance engine."""

    final_decision: str
    confidence: float | None
    explanation: Sequence[str]
    expert_results: Sequence[ExpertResult]
    total_runtime_ms: float


def analyze_transaction(
    request: FinancialRequest,
    on_progress: Callable[[str], None] | None = None,
) -> AnalysisResult:
    """Run the rule-driven experts and return the existing render-ready shape."""
    emit = on_progress or (lambda _: None)
    started = perf_counter()
    emit("Validating request")
    emit("Loading governance rules")
    experts = (PolicyExpert(), FraudExpert(), RiskExpert(), ComplianceExpert(), SpendExpert(), AuditExpert())
    emit("Routing relevant experts")
    outputs = []
    for expert in experts:
        emit(f"Running {expert.expert_type.value.title()} Expert")
        expert_started = perf_counter()
        output = expert.evaluate(request)
        outputs.append((output, (perf_counter() - expert_started) * 1000))
    expert_results = tuple(ExpertResult(f"{output.expert.value.title()} Expert", output.decision.value.upper(), output.confidence, elapsed, output.metadata) for output, elapsed in outputs)
    emit("Aggregating rule results")
    precedence = (DecisionType.BLOCK, DecisionType.REVIEW, DecisionType.APPROVE)
    final = next(decision for decision in precedence if any(output.decision == decision for output, _ in outputs))
    supporting = [output for output, _ in outputs if output.decision == final and output.expert.value != "audit"]
    emit("Generating explanation")
    return AnalysisResult(
        final_decision=final.value.upper(),
        confidence=max((output.confidence for output in supporting if output.confidence is not None), default=None),
        explanation=tuple(f"{output.expert.value.title()}: {output.reasoning}" for output, _ in outputs),
        expert_results=expert_results,
        total_runtime_ms=(perf_counter() - started) * 1000,
    )
