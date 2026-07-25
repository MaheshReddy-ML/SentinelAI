from collections.abc import Iterator

import pytest

from models.llm.local_provider import LocalMLXProvider
from models.llm.parser import RequestValidationError


VALID_REQUEST = '''{"request_id":"r-1","user_id":"u-1","session_id":"s-1","intent":"customer_request","action":"travel_booking","transaction":{"amount":1250,"currency":"USD","merchant":"Northstar Travel"},"context":{"location":"US"},"metadata":{"category":"travel","payment_method":"corporate_card"},"timestamp":"2026-07-25T10:30:00+00:00"}'''


def _responses(values: list[str]) -> Iterator[str]:
    yield from values


def test_provider_returns_validated_financial_request() -> None:
    provider = LocalMLXProvider(generate_text=lambda _: VALID_REQUEST)

    request = provider.generate_request("Book a business flight to New York for $1250.")

    assert request.action.value == "travel_booking"
    assert request.transaction.amount == 1250


def test_provider_retries_once_after_malformed_json() -> None:
    responses = _responses(["not json", VALID_REQUEST])
    provider = LocalMLXProvider(generate_text=lambda _: next(responses))

    request = provider.generate_request("Book a flight")

    assert request.request_id != "r-1"
    assert request.request_id


def test_provider_reports_structured_error_after_retry() -> None:
    provider = LocalMLXProvider(generate_text=lambda _: "[]")

    with pytest.raises(RequestValidationError, match="after one retry"):
        provider.generate_request("Book a flight")
