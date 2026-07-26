"""Interactive input collection and file-to-schema conversion."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import typer
from pydantic import ValidationError

from schemas.enums import ActionType, IntentType
from schemas.request import FinancialRequest, RequestContext, TransactionDetails


@dataclass(frozen=True)
class LoadedBatch:
    """Valid requests and readable row-level validation errors from one file."""

    requests: list[FinancialRequest]
    errors: list[str]


def collect_request() -> FinancialRequest:
    """Collect a financial request through concise, validated prompts."""
    amount = typer.prompt("Amount", type=float)
    currency = typer.prompt("Currency", default="USD").upper()
    merchant = typer.prompt("Merchant")
    category = typer.prompt("Category", default="general")
    country = typer.prompt("Country", default="US").upper()
    payment_method = typer.prompt("Payment method", default="card")
    timestamp = typer.prompt("Timestamp (ISO 8601, blank for now)", default="")
    user_id = typer.prompt("User ID (optional)", default="")
    return _build_request(
        {
            "amount": amount,
            "currency": currency,
            "merchant": merchant,
            "category": category,
            "country": country,
            "payment_method": payment_method,
            "timestamp": timestamp or datetime.now().astimezone().isoformat(),
            "user_id": user_id or "anonymous",
        }
    )


def load_batch(path: Path) -> LoadedBatch:
    """Load one object, an object batch, or JSON Lines into request contracts."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        return LoadedBatch([], [f"Unable to read file: {error}"])
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        try:
            payload = [json.loads(line) for line in raw.splitlines() if line.strip()]
        except json.JSONDecodeError:
            return LoadedBatch([], [f"Malformed JSON: {error.msg}"])
    if isinstance(payload, dict) and "requests" in payload:
        payload = payload["requests"]
    items = [payload] if isinstance(payload, dict) else payload
    if not isinstance(items, list) or not items:
        return LoadedBatch([], ["Expected one object, a non-empty JSON array, or a 'requests' array."])
    requests: list[FinancialRequest] = []
    errors: list[str] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
                errors.append(f"Row {index}: expected a JSON object")
                continue
        try:
            requests.append(_build_request(item))
        except (TypeError, ValueError, ValidationError) as error:
            if isinstance(error, ValidationError):
                issue = error.errors()[0]
                errors.append(f"Row {index}: {'.'.join(str(part) for part in issue['loc'])} — {issue['msg']}")
            else:
                errors.append(f"Row {index}: {str(error).splitlines()[0]}")
    return LoadedBatch(requests, errors)


def load_requests(path: Path) -> list[FinancialRequest]:
    """Load all valid requests or present a concise file-level error."""
    batch = load_batch(path)
    if not batch.requests:
        raise typer.BadParameter("; ".join(batch.errors) or "No valid requests found.")
    return batch.requests


def load_request(path: Path) -> FinancialRequest:
    """Load exactly one request for code paths that require a single object."""
    requests = load_requests(path)
    if len(requests) != 1:
        raise typer.BadParameter("Expected one request; use load_requests() for a batch.")
    return requests[0]


def _build_request(payload: dict[str, object]) -> FinancialRequest:
    """Map either compact CLI JSON or the native schema JSON to a request."""
    if {"request_id", "session_id", "intent", "action"}.issubset(payload):
        return FinancialRequest.model_validate(payload)

    timestamp = payload.get("timestamp") or datetime.now().astimezone().isoformat()
    category = str(payload.get("category") or "general")
    action_value = str(payload.get("action") or (category if category in {item.value for item in ActionType} else ActionType.MERCHANT_PAYMENT.value))
    intent_value = str(payload.get("intent", IntentType.CUSTOMER_REQUEST.value))
    return FinancialRequest(
        request_id=str(payload.get("request_id") or uuid4()),
        user_id=str(payload.get("user_id") or "anonymous"),
        session_id=str(payload.get("session_id") or uuid4()),
        intent=IntentType(intent_value),
        action=ActionType(action_value),
        transaction=TransactionDetails(
            amount=float(payload["amount"]) if payload.get("amount") is not None else None,
            currency=str(payload.get("currency") or "USD").upper(),
            merchant=str(payload.get("merchant") or "Unspecified merchant"),
        ),
        context=RequestContext(location=str(payload.get("country") or "Unknown")),
        metadata={
            "category": category,
            "payment_method": str(payload.get("payment_method") or "unspecified"),
        },
        timestamp=timestamp,
    )
