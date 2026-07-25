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


@pytest.mark.parametrize(
    "rule_set", ["audit", "compliance", "fraud", "policy", "risk", "spend"],
)
def test_all_rule_sets_load_as_validated_rule_objects(rule_set: str) -> None:
    RuleLoader.clear_cache()

    document = RuleLoader.load_rules(rule_set)

    assert document["rules"]
    assert all(rule.rule_id for rule in document["rules"])


def test_cached_rule_documents_are_defensively_copied() -> None:
    RuleLoader.clear_cache()
    first = RuleLoader.load_rules("policy")
    first["rules"].clear()

    second = RuleLoader.load_rules("policy")

    assert second["rules"]


def test_invalid_rule_document_shape_is_rejected(tmp_path, monkeypatch) -> None:
    (tmp_path / "invalid_rules.json").write_text('{"rules": {}}', encoding="utf-8")
    monkeypatch.setattr(RuleLoader, "RULES_DIR", tmp_path)
    RuleLoader.clear_cache()

    with pytest.raises(ValueError, match="must be a list"):
        RuleLoader.load_rules("invalid")
