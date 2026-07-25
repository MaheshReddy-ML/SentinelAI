from schemas.request import FinancialRequest
from schemas.rule import Rule
from utils.condition_evaluator import ConditionEvaluator
from utils.rule_loader import RuleLoader


class RuleExecutor:
    """
    Executes a rule set against a FinancialRequest.

    Responsibilities:
    - Load rules
    - Skip disabled rules
    - Evaluate rule conditions
    - Return matching rules ordered by priority

    Does NOT:
    - Calculate risk scores
    - Make governance decisions
    - Aggregate expert outputs
    """

    def __init__(
        self,
        rule_loader: RuleLoader,
        evaluator: ConditionEvaluator,
    ):
        self.rule_loader = rule_loader
        self.evaluator = evaluator

    def execute(
        self,
        request: FinancialRequest,
        rule_file: str,
    ) -> list[Rule]:
        """
        Execute all enabled rules and return matched rules.
        """

        rule_document = self.rule_loader.load_rules(rule_file)
        rules: list[Rule] = rule_document["rules"]

        matches: list[Rule] = []

        for rule in rules:

            if not rule.enabled:
                continue

            if self._matches_action(rule, request) and self._evaluate_rule(rule, request):
                matches.append(rule)

        matches.sort(key=lambda rule: rule.priority)

        return matches

    def _evaluate_rule(
        self,
        rule: Rule,
        request: FinancialRequest,
    ) -> bool:
        """
        Evaluate a single rule.
        """

        return self.evaluator.evaluate(
            request,
            rule.conditions,
        )

    @staticmethod
    def _matches_action(rule: Rule, request: FinancialRequest) -> bool:
        """Return whether a rule applies to the request action."""
        return rule.action == "*" or rule.action == request.action.value
