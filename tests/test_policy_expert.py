from schemas.enums import ActionType, DecisionType, IntentType
from schemas.request import FinancialRequest, TransactionDetails
from models.experts.policy_expert import PolicyExpert


def _refund_request(amount: float) -> FinancialRequest:
    return FinancialRequest(
        request_id="request-1",
        user_id="user-1",
        session_id="session-1",
        intent=IntentType.CUSTOMER_REQUEST,
        action=ActionType.REFUND,
        transaction=TransactionDetails(amount=amount, currency="USD"),
    )


def test_default_review_when_no_policy_rule_matches() -> None:
    expert = PolicyExpert()
    expert.rules = []

    output = expert.evaluate(_refund_request(15_000))

    assert output.decision == DecisionType.REVIEW
    assert output.reasoning == "No matching policy rule found."


def test_policy_uses_real_request_contract_at_threshold_boundaries() -> None:
    expert = PolicyExpert()

    assert expert.evaluate(_refund_request(20_000)).decision == DecisionType.APPROVE
    assert expert.evaluate(_refund_request(20_001)).decision == DecisionType.REVIEW
    assert expert.evaluate(_refund_request(100_001)).decision == DecisionType.BLOCK
