"""
Rule Loader for SentinelAI

Responsible for:
- Loading governance rule files
- Validating rule existence
- Caching loaded rules
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class RuleLoader:
    """Loads and caches governance rule files."""

    _cache: dict[str, dict[str, Any]] = {}

    RULES_DIR = Path(__file__).resolve().parent.parent / "rules"

    @classmethod
    def load_rules(cls, rule_name: str) -> dict[str, Any]:
        if rule_name in cls._cache:
            return cls._cache[rule_name]

        file_path = cls.RULES_DIR / f"{rule_name}_rules.json"

        if not file_path.exists():
            raise FileNotFoundError(
                f"Rule file not found: {file_path}"
            )

        with file_path.open("r", encoding="utf-8") as f:
            rules = json.load(f)

        if "rules" not in rules:
            raise ValueError(
                f"Invalid rule file '{rule_name}'. Missing 'rules' key."
            )

        cls._cache[rule_name] = rules

        return rules

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache.clear()

    @classmethod
    def available_rules(cls) -> list[str]:
        return sorted(
            path.stem.replace("_rules", "")
            for path in cls.RULES_DIR.glob("*_rules.json")
        )