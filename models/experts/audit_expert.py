from models.experts.rule_expert import RuleExpert
from schemas.enums import ExpertType


class AuditExpert(RuleExpert):
    """Records audit-ready request context without changing the decision."""

    def __init__(self) -> None:
        super().__init__(ExpertType.AUDIT, "audit")

    def evaluate(self, request):
        """Audit is traceability evidence, not an independent confidence vote."""
        return super().evaluate(request).model_copy(update={"confidence": None})
