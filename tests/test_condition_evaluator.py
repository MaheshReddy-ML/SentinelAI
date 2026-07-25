import pytest

from utils.condition_evaluator import ConditionEvaluator


class DummyRequest:
    def __init__(self):
        self.action = "refund"
        self.amount = 15000
        self.country = "US"
        self.currency = "USD"
        self.category = "shopping"
        self.payment_method = "credit_card"


def test_empty_conditions():
    request = DummyRequest()

    assert ConditionEvaluator.evaluate(request, {}) is True


def test_unknown_condition():
    request = DummyRequest()

    with pytest.raises(ValueError):
        ConditionEvaluator.evaluate(
            request,
            {
                "unknown_condition": True,
            },
        )


def test_min_amount():
    request = DummyRequest()

    assert ConditionEvaluator.evaluate(
        request,
        {
            "min_amount": 10000,
        },
    )


def test_max_amount():
    request = DummyRequest()

    assert ConditionEvaluator.evaluate(
        request,
        {
            "max_amount": 20000,
        },
    )