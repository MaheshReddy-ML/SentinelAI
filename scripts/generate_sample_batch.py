"""Regenerate the committed 100-row operational batch fixture."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


def main() -> None:
    requests: list[object] = []
    base = datetime(2026, 7, 26, 9, tzinfo=timezone.utc)
    profiles = [
        ("travel_booking", 18_500, "INR", "IndiGo Airlines", "corporate_card", "IN"),
        ("merchant_payment", 45_000, "INR", "Microsoft India", "bank_transfer", "IN"),
        ("credit_limit_increase", 400_000, "INR", None, "corporate_card", "IN"),
        ("merchant_payment", 500_000, "USD", "Global Supplier Ltd", "wire_transfer", "US"),
        ("refund", 2_350, "INR", "Retail Partner", "corporate_card", "IN"),
        ("merchant_payment", 2_500_000, "INR", "Overseas Vendor", "wire_transfer", None),
        ("merchant_payment", 20_000, "USD", "Cloud Services Inc", "corporate_card", "US"),
        ("merchant_payment", 120_000, "INR", "New Device Merchant", "corporate_card", "IN"),
        ("travel_booking", 485_000, "INR", "Travel Desk", "corporate_card", "IN"),
    ]
    for index in range(1, 101):
        if index % 10 == 0:
            requests.append({"amount": -1000, "currency": "INR", "merchant": "Invalid Test Merchant", "category": "purchase", "user_id": f"emp-{index:04d}"})
            continue
        if index % 25 == 0:
            requests.append("malformed request row")
            continue
        category, amount, currency, merchant, method, country = profiles[(index - 1) % len(profiles)]
        requests.append({
            "amount": amount + (index % 5) * 500,
            "currency": currency,
            "merchant": merchant,
            "category": category,
            "country": country,
            "destination": "Bangalore" if category == "travel_booking" else None,
            "payment_method": method,
            "purpose": "Business travel" if category == "travel_booking" else "Operational expense",
            "timestamp": (base + timedelta(minutes=index)).isoformat(),
            "user_id": f"emp-{1000 + index}",
            "aml_flag": index % 17 == 0,
            "new_device": index % 13 == 0,
            "international": country is None or index % 19 == 0,
        })
    target = Path(__file__).resolve().parent.parent / "simulations" / "sample.json"
    target.write_text(json.dumps(requests, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
