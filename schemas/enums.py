from enum import Enum


# ==========================================================
# Request Enums
# ==========================================================

class ActionType(str, Enum):
    REFUND = "refund"
    CARD_REPLACEMENT = "card_replacement"
    CREDIT_LIMIT_INCREASE = "credit_limit_increase"
    TRAVEL_BOOKING = "travel_booking"
    BALANCE_INQUIRY = "balance_inquiry"
    ACCOUNT_FREEZE = "account_freeze"
    ACCOUNT_UNFREEZE = "account_unfreeze"
    MERCHANT_PAYMENT = "merchant_payment"
    DISPUTE_TRANSACTION = "dispute_transaction"


class IntentType(str, Enum):
    CUSTOMER_REQUEST = "customer_request"
    SYSTEM_REQUEST = "system_request"
    AGENT_REQUEST = "agent_request"


# ==========================================================
# Expert Enums
# ==========================================================

class ExpertType(str, Enum):
    POLICY = "policy"
    RISK = "risk"
    FRAUD = "fraud"
    COMPLIANCE = "compliance"
    SPEND = "spend"
    AUDIT = "audit"


# ==========================================================
# Decision Enums
# ==========================================================

class DecisionType(str, Enum):
    APPROVE = "approve"
    BLOCK = "block"
    REVIEW = "review"
    ESCALATE = "escalate"


class PolicyResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


# ==========================================================
# Risk Enums
# ==========================================================

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ==========================================================
# Governance Enums
# ==========================================================

class GovernanceStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutionMode(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"
    HYBRID = "hybrid"


# ==========================================================
# Explainability Enums
# ==========================================================

class ExplanationLevel(str, Enum):
    BASIC = "basic"
    DETAILED = "detailed"
    AUDIT = "audit"
# ==========================================================
# Severity Enums
# ==========================================================
class SeverityLevel(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# ==========================================================
# Routing Enums
# ==========================================================
class RoutingStrategy(str, Enum):
    STATIC = "static"
    ADAPTIVE = "adaptive"
    HYBRID = "hybrid"