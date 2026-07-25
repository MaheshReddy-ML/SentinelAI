from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import ValidationError

from schemas.enums import ActionType, IntentType
from schemas.request import FinancialRequest


class RequestValidationError(ValueError):
    """A user-safe error produced when local-model output is not a request."""


def parse_request_json(response: str, user_id: str | None = None, source_prompt: str = "") -> FinancialRequest:
    """Extract one JSON object and validate it against the existing Pydantic contract."""
    start, end = response.find("{"), response.rfind("}")
    if start < 0 or end < start:
        raise RequestValidationError("The local model did not return a JSON object.")
    try:
        payload = json.loads(response[start : end + 1])
    except json.JSONDecodeError as error:
        raise RequestValidationError("The local model returned malformed JSON.") from error
    if not isinstance(payload, dict):
        raise RequestValidationError("The local model response must be a JSON object.")

    payload["request_id"] = str(uuid4())
    payload["user_id"] = user_id or os.getenv("SENTINEL_USER_ID") or "Unknown"
    payload["session_id"] = str(uuid4())
    payload["intent"] = IntentType.CUSTOMER_REQUEST.value
    payload.setdefault("action", ActionType.MERCHANT_PAYMENT.value)
    payload["timestamp"] = datetime.now(UTC).isoformat()
    transaction = payload.setdefault("transaction", {})
    if not isinstance(transaction, dict):
        raise RequestValidationError("The extracted transaction must be an object.")
    for field in ("merchant", "amount", "currency", "transaction_id"):
        if transaction.get(field) in ("Unknown", "Not Provided", "null", "N/A", ""):
            transaction[field] = None
    explicit, inferred = _explicit_entities(source_prompt)
    # User text wins over the model for financial facts.  Values not present in
    # the prompt are deliberately erased rather than guessed by the model.
    transaction.update(explicit["transaction"])
    payload.setdefault("context", {})["location"] = explicit["country"]
    metadata = payload.setdefault("metadata", {})
    for key in ("category", "payment_method", "destination", "travel_date", "purpose", "description"):
        metadata.pop(key, None)
    metadata.update(explicit["metadata"])
    metadata["_extraction"] = {"explicit": sorted(explicit["fields"]), "inferred": sorted(inferred)}
    if category := metadata.get("category"):
        payload["action"] = category
    try:
        return FinancialRequest.model_validate(payload)
    except ValidationError as error:
        raise RequestValidationError(f"The extracted request is invalid: {error.errors()[0]['msg']}") from error


def _explicit_entities(prompt: str) -> tuple[dict[str, object], set[str]]:
    """Extract only auditable, explicitly stated financial entities from text."""
    text = prompt.strip()
    lower = text.lower()
    transaction: dict[str, object] = {"merchant": None, "amount": None, "currency": None, "transaction_id": None}
    metadata: dict[str, object] = {"description": text} if text else {}
    fields: set[str] = {"description"} if text else set()
    inferred: set[str] = set()
    currency = "INR" if "₹" in text or re.search(r"\bINR\b", text, re.I) else "USD" if "$" in text or re.search(r"\bUSD\b", text, re.I) else "EUR" if "€" in text or re.search(r"\bEUR\b", text, re.I) else "GBP" if "£" in text or re.search(r"\bGBP\b", text, re.I) else None
    amount_match = re.search(r"(?:₹|\$|€|£)?\s*(\d+(?:\.\d+)?)\s*(lakh(?:s)?|lac(?:s)?|l\b)?", lower)
    if amount_match:
        amount = float(amount_match.group(1))
        if amount_match.group(2):
            amount *= 100_000
        transaction["amount"] = int(amount) if amount.is_integer() else amount
        fields.add("amount")
    if currency:
        transaction["currency"] = currency
        fields.add("currency")
    if "corporate card" in lower:
        metadata["payment_method"] = "corporate_card"
        fields.add("payment_method")
    action_map = (("credit card limit", "credit_limit_increase"), ("credit limit", "credit_limit_increase"), ("flight", "travel_booking"), ("travel", "travel_booking"), ("refund", "refund"), ("merchant payment", "merchant_payment"), ("wire transfer", "merchant_payment"), ("transfer", "merchant_payment"))
    for phrase, category in action_map:
        if phrase in lower:
            metadata["category"] = category
            fields.add("category")
            break
    destination = re.search(r"\b(?:to|for)\s+([A-Z][A-Za-z .'-]{1,40}?)(?:\s+(?:tomorrow|on|for|using)|[,.]|$)", text)
    if destination and "flight" in lower:
        metadata["destination"] = destination.group(1).strip()
        fields.add("destination")
    if "tomorrow" in lower:
        metadata["travel_date"] = "tomorrow"
        fields.add("travel_date")
    if "business" in lower:
        metadata["purpose"] = "business"
        fields.add("purpose")
    if "overseas" in lower or "international" in lower:
        metadata["international"] = True
        fields.add("international")
    return {"transaction": transaction, "metadata": metadata, "country": None, "fields": fields}, inferred
