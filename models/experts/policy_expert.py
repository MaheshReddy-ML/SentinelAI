from __future__ import annotations

from models.base.base_expert import BaseExpert
from schemas.enums import (
    DecisionType,
    ExpertType,
    PolicyResult,
    RiskLevel,
)
from schemas.expert_output import ExpertOutput
from schemas.request import FinancialRequest
from schemas.rule import Rule
from utils.condition_evaluator import ConditionEvaluator
from utils.rule_loader import RuleLoader


class PolicyExpert(BaseExpert):
    """
    Governance expert responsible for evaluating policy rules.
    """

    RULE_SET = "policy"

    @property
    def expert_type(self) -> ExpertType:
        """Returns the expert type."""
        return ExpertType.POLICY

    def __init__(self) -> None:
        """Load and cache all enabled policy rules."""

        rule_data = RuleLoader.load_rules(self.RULE_SET)

        self.rules: list[Rule] = sorted(
            (
                rule
                for rule in rule_data["rules"]
                if rule.enabled
            ),
            key=lambda rule: rule.priority,
        )

    def evaluate(
        self,
        request: FinancialRequest,
    ) -> ExpertOutput:
        """
        Evaluate a financial request against policy rules.
        Returns the first matching rule.
        """

        for rule in self.rules:

            if not self._matches_action(request, rule):
                continue

            if not ConditionEvaluator.evaluate(
                request,
                rule.conditions,
            ):
                continue

            return self._build_output(rule)

        return self._default_output()

    def _matches_action(
        self,
        request: FinancialRequest,
        rule: Rule,
    ) -> bool:
        """Check whether the request action matches the rule."""

        return request.action.value == rule.action

    def _build_output(
        self,
        rule: Rule,
    ) -> ExpertOutput:
        """Convert a matching rule into an ExpertOutput."""

        return ExpertOutput(
            expert=self.expert_type,
            decision=rule.decision or DecisionType.REVIEW,
            confidence=rule.confidence if rule.confidence is not None else 0.0,
            score=100.0,
            risk_level=rule.severity,
            policy_result=(
                PolicyResult.PASS
                if rule.decision == DecisionType.APPROVE
                else PolicyResult.FAIL
            ),
            reasoning=rule.reason,
            metadata={
                "rule_id": rule.rule_id,
                "rule_name": rule.name,
                "priority": rule.priority,
            },
        )

    def _default_output(self) -> ExpertOutput:
        """Return the default output when no rule matches."""

        return ExpertOutput(
            expert=self.expert_type,
            decision=DecisionType.REVIEW,
            confidence=None,
            score=0.0,
            risk_level=RiskLevel.MEDIUM,
            policy_result=PolicyResult.FAIL,
            reasoning="No matching policy rule found.",
            metadata={},
        )
