from models.experts.risk_expert import RiskExpert
from schemas.enums import ActionType, DecisionType, IntentType, RiskLevel
from schemas.request import FinancialRequest, TransactionDetails
from utils.condition_evaluator import ConditionEvaluator
from utils.rule_executor import RuleExecutor
from utils.rule_loader import RuleLoader


def _request(action: ActionType, amount: float) -> FinancialRequest:
    return FinancialRequest(
        request_id="request-1",
        user_id="user-1",
        session_id="session-1",
        intent=IntentType.CUSTOMER_REQUEST,
        action=action,
        transaction=TransactionDetails(amount=amount, currency="USD"),
    )


def test_rule_executor_returns_priority_ordered_typed_matches() -> None:
    executor = RuleExecutor(RuleLoader(), ConditionEvaluator())

    matches = executor.execute(_request(ActionType.REFUND, 80_000), "risk")

    assert [rule.rule_id for rule in matches] == ["RSK-001", "RSK-000"]


def test_risk_expert_generates_a_schema_valid_high_risk_review() -> None:
    output = RiskExpert().evaluate(_request(ActionType.REFUND, 80_000))

    assert output.decision == DecisionType.REVIEW
    assert output.risk_level == RiskLevel.HIGH
    assert output.score == 60
    assert output.confidence == 0.92
    assert output.metadata["rule_ids"] == ["RSK-001", "RSK-000"]


def test_risk_expert_blocks_a_critical_transaction() -> None:
    output = RiskExpert().evaluate(_request(ActionType.MERCHANT_PAYMENT, 600_000))

    assert output.decision == DecisionType.BLOCK
    assert output.risk_level == RiskLevel.CRITICAL
