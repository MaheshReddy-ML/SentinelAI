import json


def build_request_prompt(user_prompt: str) -> str:
    """Build a deterministic extraction-only instruction for the local model."""
    schema = {
        "request_id": "string",
        "user_id": "string",
        "session_id": "string",
        "intent": "customer_request|system_request|agent_request",
        "action": "refund|card_replacement|credit_limit_increase|travel_booking|balance_inquiry|account_freeze|account_unfreeze|merchant_payment|dispute_transaction",
        "transaction": {"transaction_id": "string|null", "merchant": "string|null", "amount": "number|null", "currency": "ISO 4217 string|null"},
        "context": {"ip_address": "string|null", "device": "string|null", "location": "country string|null", "channel": "string|null"},
        "metadata": {"category": "string", "payment_method": "string", "kyc_verified": "boolean|null", "aml_flag": "boolean|null", "new_device": "boolean|null", "international": "boolean|null"},
        "timestamp": "ISO 8601 timestamp",
    }
    return (
        "You are a strict information-extraction component for a financial governance system. "
        "You never approve, block, review, score, or recommend anything. Infer only facts stated "
        "by the user. Return one JSON object and no markdown. If a required fact is unknown, use "
        "reasonable neutral identifiers and null optional values; choose the closest action. "
        "Do not show reasoning, analysis, or <think> tags. Output JSON immediately.\n"
        f"Required JSON shape: {json.dumps(schema)}\n"
        f"User request: {user_prompt}\n/no_think"
    )
