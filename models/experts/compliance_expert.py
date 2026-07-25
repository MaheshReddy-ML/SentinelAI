from models.experts.rule_expert import RuleExpert
from schemas.enums import ExpertType


class ComplianceExpert(RuleExpert):
    def __init__(self) -> None:
        super().__init__(ExpertType.COMPLIANCE, "compliance")
