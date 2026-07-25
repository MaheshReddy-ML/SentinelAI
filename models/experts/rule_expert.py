from models.base.base_expert import BaseExpert
from schemas.enums import DecisionType, ExpertType
from schemas.expert_output import ExpertOutput
from schemas.request import FinancialRequest
from utils.condition_evaluator import ConditionEvaluator
from utils.rule_executor import RuleExecutor
from utils.rule_loader import RuleLoader


class RuleExpert(BaseExpert):
    """Small reusable adapter for rule sets that directly recommend a decision."""

    def __init__(self, expert_type: ExpertType, rule_set: str) -> None:
        self._expert_type = expert_type
        self._rule_set = rule_set
        self._executor = RuleExecutor(RuleLoader(), ConditionEvaluator())

    @property
    def expert_type(self) -> ExpertType:
        return self._expert_type

    def evaluate(self, request: FinancialRequest) -> ExpertOutput:
        matches = self._executor.execute(request, self._rule_set)
        if not matches:
            return ExpertOutput(expert=self.expert_type, decision=DecisionType.REVIEW, confidence=None, reasoning=f"No governance policy currently exists for {request.action.value}; manual review is required.", metadata={"matched_rule_ids": []})
        rank = {DecisionType.APPROVE: 0, DecisionType.REVIEW: 1, DecisionType.BLOCK: 2, DecisionType.ESCALATE: 2}
        rule = max(matches, key=lambda item: rank.get(item.decision or DecisionType.REVIEW, 1))
        return ExpertOutput(expert=self.expert_type, decision=rule.decision or DecisionType.REVIEW, confidence=rule.confidence, risk_level=rule.severity, reasoning=" ".join(item.reason for item in matches), metadata={"rule_id": rule.rule_id, "matched_rule_ids": [item.rule_id for item in matches], "evaluated_rule_ids": [item.rule_id for item in self._executor.rule_loader.load_rules(self._rule_set)["rules"]]})
