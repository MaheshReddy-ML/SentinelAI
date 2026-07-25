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
        return request.transaction.amount is not None and request.transaction.amount >= value

    @staticmethod
    def _max_amount(
        request: FinancialRequest,
        value: float,
    ) -> bool:
        return request.transaction.amount is not None and request.transaction.amount <= value

    @staticmethod
    def _country(
        request: FinancialRequest,
        value: str,
    ) -> bool:
        return request.context.location == value

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
        return request.metadata.get("category") == value

    @staticmethod
    def _payment_method(
        request: FinancialRequest,
        value: str,
    ) -> bool:
        return request.metadata.get("payment_method") == value

    @staticmethod
    def _metadata_value(
        request: FinancialRequest,
        key: str,
        value: Any,
    ) -> bool:
        return request.metadata.get(key) == value

    @staticmethod
    def _kyc_verified(request: FinancialRequest, value: bool) -> bool:
        return ConditionEvaluator._metadata_value(request, "kyc_verified", value)

    @staticmethod
    def _aml_flag(request: FinancialRequest, value: bool) -> bool:
        return ConditionEvaluator._metadata_value(request, "aml_flag", value)

    @staticmethod
    def _new_device(request: FinancialRequest, value: bool) -> bool:
        return ConditionEvaluator._metadata_value(request, "new_device", value)

    @staticmethod
    def _international(request: FinancialRequest, value: bool) -> bool:
        return ConditionEvaluator._metadata_value(request, "international", value)

    _HANDLERS: dict[str, ConditionHandler] = {
        "min_amount": _min_amount.__func__,
        "max_amount": _max_amount.__func__,
        "country": _country.__func__,
        "currency": _currency.__func__,
        "category": _category.__func__,
        "payment_method": _payment_method.__func__,
        "kyc_verified": _kyc_verified.__func__,
        "aml_flag": _aml_flag.__func__,
        "new_device": _new_device.__func__,
        "international": _international.__func__,
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
