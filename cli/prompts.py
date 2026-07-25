"""Interactive input collection and file-to-schema conversion."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import typer
from pydantic import ValidationError

from schemas.enums import ActionType, IntentType
from schemas.request import FinancialRequest, RequestContext, TransactionDetails


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


def load_request(path: Path) -> FinancialRequest:
    """Load a JSON object and convert its CLI fields into the request contract."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise typer.BadParameter(f"Unable to read {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise typer.BadParameter(f"{path} is not valid JSON: {error.msg}") from error
    if not isinstance(payload, dict):
        raise typer.BadParameter("The sample file must contain one JSON object.")
    try:
        return _build_request(payload)
    except (TypeError, ValueError, ValidationError) as error:
        raise typer.BadParameter(f"Invalid request data: {error}") from error


def _build_request(payload: dict[str, object]) -> FinancialRequest:
    """Map either compact CLI JSON or the native schema JSON to a request."""
    if {"request_id", "session_id", "intent", "action"}.issubset(payload):
        return FinancialRequest.model_validate(payload)

    timestamp = payload.get("timestamp") or datetime.now().astimezone().isoformat()
    action_value = str(payload.get("action", ActionType.MERCHANT_PAYMENT.value))
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
            "category": str(payload.get("category") or "general"),
            "payment_method": str(payload.get("payment_method") or "unspecified"),
        },
        timestamp=timestamp,
    )
