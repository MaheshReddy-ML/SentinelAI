from __future__ import annotations

from collections.abc import Callable
from typing import Any

from schemas.request import FinancialRequest

ConditionHandler = Callable[[FinancialRequest, Any], bool]


class ConditionEvaluator:
    """
    Evaluates rule conditions against a FinancialRequest.

    Every condition inside the JSON must evaluate to True
    for the rule to match.
    """

    @staticmethod
    def _min_amount(
        request: FinancialRequest,
        value: float,
    ) -> bool:
        return request.transaction.amount >= value

    @staticmethod
    def _max_amount(
        request: FinancialRequest,
        value: float,
    ) -> bool:
        return request.transaction.amount <= value

    @staticmethod
    def _country(
        request: FinancialRequest,
        value: str,
    ) -> bool:
        return request.transaction.country == value

    @staticmethod
    def _currency(
        request: FinancialRequest,
        value: str,
    ) -> bool:
        return request.transaction.currency == value

    @staticmethod
    def _category(
        request: FinancialRequest,
        value: str,
    ) -> bool:
        return request.transaction.category == value

    @staticmethod
    def _payment_method(
        request: FinancialRequest,
        value: str,
    ) -> bool:
        return request.transaction.payment_method == value

    _HANDLERS: dict[str, ConditionHandler] = {
        "min_amount": _min_amount.__func__,
        "max_amount": _max_amount.__func__,
        "country": _country.__func__,
        "currency": _currency.__func__,
        "category": _category.__func__,
        "payment_method": _payment_method.__func__,
    }

    @classmethod
    def evaluate(
        cls,
        request: FinancialRequest,
        conditions: dict[str, Any],
    ) -> bool:
        """
        Evaluate all conditions for a rule.

        Returns True only if every condition passes.
        """

        if not conditions:
            return True

        for key, value in conditions.items():

            handler = cls._HANDLERS.get(key)

            if handler is None:
                supported = ", ".join(sorted(cls._HANDLERS))

                raise ValueError(
                    f"Unsupported condition '{key}'. "
                    f"Supported conditions: {supported}"
                )

            if not handler(request, value):
                return False

        return True