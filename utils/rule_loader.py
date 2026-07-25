"""
Rule Loader for SentinelAI

Responsible for:
- Loading governance rule files
- Validating rule existence
- Caching loaded rules
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from schemas.rule import Rule


class RuleLoader:
    """Loads and caches governance rule files."""

    _cache: dict[str, dict[str, Any]] = {}

    RULES_DIR = Path(__file__).resolve().parent.parent / "rules"

    @classmethod
    def load_rules(cls, rule_name: str) -> dict[str, Any]:
        if rule_name in cls._cache:
            return deepcopy(cls._cache[rule_name])

        file_path = cls.RULES_DIR / f"{rule_name}_rules.json"

        if not file_path.exists():
            raise FileNotFoundError(
                f"Rule file not found: {file_path}"
            )

        with file_path.open("r", encoding="utf-8") as f:
            rule_document = json.load(f)

        if not isinstance(rule_document, dict):
            raise ValueError(f"Invalid rule file '{rule_name}'. Expected a JSON object.")

        if "rules" not in rule_document:
            raise ValueError(
                f"Invalid rule file '{rule_name}'. Missing 'rules' key."
            )

        raw_rules = rule_document["rules"]
        if not isinstance(raw_rules, list):
            raise ValueError(f"Invalid rule file '{rule_name}'. 'rules' must be a list.")

        try:
            rules = [Rule.model_validate(rule) for rule in raw_rules]
        except ValidationError as error:
            raise ValueError(f"Invalid rule file '{rule_name}': {error}") from error

        validated_document = {**rule_document, "rules": rules}
        cls._cache[rule_name] = validated_document

        return deepcopy(validated_document)

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache.clear()

    @classmethod
    def available_rules(cls) -> list[str]:
        return sorted(
            path.stem.replace("_rules", "")
            for path in cls.RULES_DIR.glob("*_rules.json")
        )
