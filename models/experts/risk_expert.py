from models.base.base_expert import BaseExpert
from schemas.enums import DecisionType, ExpertType, RiskLevel
from schemas.expert_output import ExpertOutput
from schemas.request import FinancialRequest
from utils.condition_evaluator import ConditionEvaluator
from utils.rule_engine import RiskEngine
from utils.rule_executor import RuleExecutor
from utils.rule_loader import RuleLoader


class RiskExpert(BaseExpert):
    """Expert responsible for evaluating transaction risk."""

    RULE_SET = "risk"

    def __init__(self) -> None:
        self._executor = RuleExecutor(RuleLoader(), ConditionEvaluator())

    @property
    def name(self) -> str:
        return "risk_expert"

    @property
    def expert_type(self) -> ExpertType:
        return ExpertType.RISK

    def evaluate(self, request: FinancialRequest) -> ExpertOutput:
        """
        Evaluate the transaction risk.

        This expert only assesses risk and provides supporting evidence.
        It does not make the final governance decision.
        """

        assessment = RiskEngine.assess(self._executor.execute(request, self.RULE_SET))
        decision = {
            RiskLevel.LOW: DecisionType.APPROVE,
            RiskLevel.MEDIUM: DecisionType.REVIEW,
            RiskLevel.HIGH: DecisionType.REVIEW,
            RiskLevel.CRITICAL: DecisionType.BLOCK,
        }[assessment.risk_level]

        return ExpertOutput(
            expert=self.expert_type,
            decision=decision,
            confidence=assessment.confidence if assessment.metadata["matched_rules"] else None,
            score=assessment.score,
            risk_level=assessment.risk_level,
            reasoning=(
                "; ".join(assessment.reasoning)
                if assessment.reasoning
                else "No high-risk rules triggered."
            ),
            metadata=assessment.metadata,
        )
