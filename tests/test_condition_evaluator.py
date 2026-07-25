import pytest

from schemas.enums import ActionType, IntentType
from schemas.request import FinancialRequest, RequestContext, TransactionDetails
from utils.condition_evaluator import ConditionEvaluator


@pytest.fixture
def financial_request() -> FinancialRequest:
    return FinancialRequest(
        request_id="request-1",
        user_id="user-1",
        session_id="session-1",
        intent=IntentType.CUSTOMER_REQUEST,
        action=ActionType.REFUND,
        transaction=TransactionDetails(amount=15_000, currency="USD"),
        context=RequestContext(location="US"),
        metadata={
            "category": "shopping",
            "payment_method": "credit_card",
            "kyc_verified": False,
        },
    )


def test_empty_conditions_match(financial_request: FinancialRequest) -> None:
    assert ConditionEvaluator.evaluate(financial_request, {}) is True


def test_unknown_condition_is_a_configuration_error(financial_request: FinancialRequest) -> None:
    with pytest.raises(ValueError, match="Unsupported condition"):
        ConditionEvaluator.evaluate(financial_request, {"unknown_condition": True})


def test_nested_request_fields_and_metadata_are_evaluated(
    financial_request: FinancialRequest,
) -> None:
    assert ConditionEvaluator.evaluate(
        financial_request,
        {
            "min_amount": 10_000,
            "max_amount": 20_000,
            "country": "US",
            "currency": "USD",
            "category": "shopping",
            "payment_method": "credit_card",
            "kyc_verified": False,
        },
    )


def test_missing_amount_does_not_match_numeric_conditions(
    financial_request: FinancialRequest,
) -> None:
    financial_request.transaction.amount = None

    assert ConditionEvaluator.evaluate(financial_request, {"min_amount": 1}) is False
    assert ConditionEvaluator.evaluate(financial_request, {"max_amount": 1}) is False
