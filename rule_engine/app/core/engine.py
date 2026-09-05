"""
Rule Engine Core Orchestrator.
Coordinates the end-to-end Legal Metrology evaluation flow.
"""

from typing import List, Optional
from app.models.product import EvaluateProductRequest
from app.models.compliance import EvaluateComplianceResponse
from app.core.interface import AbstractRule
from app.core.selector import RuleSelector
from app.core.executor import RuleExecutor
from app.generator.summary_generator import ComplianceResultGenerator
from app.rules.base import RuleRegistry


class RuleEngine:
    """
    Core Rule Engine coordinator orchestrating the generic pipeline flow:
    Structured Product Data -> Rule Selector -> Applicable Rules -> Rule Executor -> Individual Results -> Compliance Summary.
    """

    def __init__(
        self,
        rules: Optional[List[AbstractRule]] = None,
        selector: Optional[RuleSelector] = None,
        executor: Optional[RuleExecutor] = None,
        generator: Optional[ComplianceResultGenerator] = None,
    ):
        registered_rules = rules if rules is not None else RuleRegistry.get_all_rules()
        self.rules = registered_rules
        self.selector = selector or RuleSelector(available_rules=registered_rules)
        self.executor = executor or RuleExecutor()
        self.generator = generator or ComplianceResultGenerator()

    def evaluate(self, product: EvaluateProductRequest) -> EvaluateComplianceResponse:
        """
        Main entry point for product compliance evaluation.
        
        Generic Process:
        1. Receive structured product data payload (EvaluateProductRequest)
        2. Get rules for evaluation (RuleSelector)
        3. Execute rules sequentially/safely (RuleExecutor)
           - Evaluates applicability (is_applicable -> NOT_APPLICABLE if False)
           - Evaluates statutory check (validate -> PASS, FAIL, or MANUAL_REVIEW)
        4. Collect all individual rule results
        5. Generate overall compliance summary & violations (ComplianceResultGenerator)
        """
        # Step 2: Get rules for evaluation
        target_rules = self.selector.get_rules_for_evaluation(product)

        # Step 3 & 4: Execute rules (applicability + validation)
        rule_results = self.executor.execute_rules(target_rules, product)

        # Build remediation hint map from rule definitions
        remediation_map = {
            r.rule_id: r.remediation_hint
            for r in target_rules
            if hasattr(r, "remediation_hint") and r.remediation_hint
        }

        # Step 5: Aggregate into Compliance Summary Response
        return self.generator.generate_report(product, rule_results, remediation_map)

