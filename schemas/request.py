from datetime import UTC, datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from schemas.enums import ActionType, IntentType


# ==========================
# Nested Schemas
# ==========================

class TransactionDetails(BaseModel):
    transaction_id: Optional[str] = Field(
        default=None,
        description="Unique transaction identifier"
    )

    merchant: Optional[str] = Field(
        default=None,
        description="Merchant involved in the transaction"
    )

    amount: Optional[float] = Field(
        default=None,
        gt=0,
        description="Transaction amount"
    )

    currency: Optional[str] = Field(
        default=None,
        description="Currency code (e.g. INR, USD)"
    )


class RequestContext(BaseModel):
    ip_address: Optional[str] = Field(
        default=None,
        description="IP address of the requester"
    )

    device: Optional[str] = Field(
        default=None,
        description="Device information"
    )

    location: Optional[str] = Field(
        default=None,
        description="Geographical location"
    )

    channel: Optional[str] = Field(
        default=None,
        description="Request source (Web, Mobile, API, etc.)"
    )


# ==========================
# Main Request Schema
# ==========================

class FinancialRequest(BaseModel):
    """
    Incoming request received by SentinelAI before
    governance evaluation begins.
    """

    request_id: str = Field(
        ...,
        description="Unique request identifier"
    )

    user_id: str = Field(
        ...,
        description="Unique user identifier"
    )

    session_id: str = Field(
        ...,
        description="Current session identifier"
    )

    intent: IntentType = Field(
        ...,
        description="High-level request intent"
    )

    action: ActionType = Field(
        ...,
        description="Requested financial action"
    )

    transaction: TransactionDetails = Field(
        default_factory=TransactionDetails
    )

    context: RequestContext = Field(
        default_factory=RequestContext
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional system metadata"
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Request creation timestamp"
    )
