"""
Rule Selector component.
Identifies active rules for evaluation.
"""

from typing import List
from app.core.interface import AbstractRule
from app.models.product import EvaluateProductRequest


class RuleSelector:
    """
    Component responsible for retrieving rules for execution.
    """

    def __init__(self, available_rules: List[AbstractRule] = None):
        self.available_rules = available_rules or []

    def get_rules_for_evaluation(self, product: EvaluateProductRequest) -> List[AbstractRule]:
        """
        Returns all registered rules. Applicability is evaluated dynamically per rule.
        """
        return self.available_rules

