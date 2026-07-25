from pathlib import Path

import pytest

from utils.rule_loader import RuleLoader


def test_load_policy_rules():
    """Policy rules should load successfully."""

    rules = RuleLoader.load_rules("policy")

    assert isinstance(rules, dict)
    assert "rules" in rules
    assert len(rules["rules"]) > 0


def test_invalid_rule_file():
    """Loading an unknown rule file should fail."""

    with pytest.raises(FileNotFoundError):
        RuleLoader.load_rules("unknown_rules")