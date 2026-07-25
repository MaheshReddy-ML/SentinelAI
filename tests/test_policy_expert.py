import pytest

from models.experts.policy_expert import PolicyExpert
from schemas.enums import (
    DecisionType,
    ExpertType,
)


class DummyRequest:
    action = "refund"
    amount = 15000


def test_default_review(monkeypatch):
    """No matching rules should return REVIEW."""

    expert = PolicyExpert()

    expert.rules = []

    output = expert.evaluate(DummyRequest())

    assert output.expert == ExpertType.POLICY
    assert output.decision == DecisionType.REVIEW


def test_matching_rule(monkeypatch):
    """A matching rule should be returned."""

    expert = PolicyExpert()

    rule = expert.rules[0]

    monkeypatch.setattr(
        expert,
        "_matches_action",
        lambda *_: True,
    )

    monkeypatch.setattr(
        "utils.condition_evaluator.ConditionEvaluator.evaluate",
        lambda *_: True,
    )

    output = expert.evaluate(DummyRequest())

    assert output.decision == rule.decision
    assert output.confidence == rule.confidence