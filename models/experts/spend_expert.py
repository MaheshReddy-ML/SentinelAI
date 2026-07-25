from models.experts.rule_expert import RuleExpert
from schemas.enums import ExpertType


class SpendExpert(RuleExpert):
    def __init__(self) -> None:
        super().__init__(ExpertType.SPEND, "spend")
