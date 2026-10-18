"""
Legal Metrology Compliance Rule: Declaration Placement & Principal Display Panel (PDP) Rule.
Statutory Provision: Rule 6 & Rule 7 [VERIFY against official Rules text], Legal Metrology (Packaged Commodities) Rules, 2011.
"""

from typing import Optional
from app.core.interface import AbstractRule
from app.models.product import EvaluateProductRequest
from app.models.rule_result import IndividualRuleResult, RuleStatus, RuleSeverity
from app.rules.base import RuleRegistry


@RuleRegistry.register
class DeclarationPlacementRule(AbstractRule):
    """
    Validates placement of mandatory declarations on the Principal Display Panel (PDP).
    Legal Reference: Rule 6 & Rule 7, Legal Metrology (Packaged Commodities) Rules, 2011.
    """

    @property
    def rule_id(self) -> str:
        return "LM-RULE-PLACE-013"

    @property
    def rule_name(self) -> str:
        return "Declaration Placement & PDP Panel Check"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    @property
    def target_field(self) -> str:
        return "declarationPlacement"

    @property
    def remediation_hint(self) -> Optional[str]:
        return "Ensure all mandatory statutory declarations are grouped together and prominently displayed on the Principal Display Panel (PDP)."

    def is_applicable(self, product: EvaluateProductRequest) -> bool:
        """
        Applicability:
        - Applicable when declarationPlacement string OR isPDPPlacementValid boolean is supplied.
        - Returns False (NOT_APPLICABLE) when no placement metadata is provided.
        """
        if product.declarationPlacement and product.declarationPlacement.strip():
            return True
        if product.isPDPPlacementValid is not None:
            return True
        return False

    def validate(self, product: EvaluateProductRequest) -> IndividualRuleResult:
        if product.isPDPPlacementValid is True:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.PASS,
                severity=self.severity,
                message="Mandatory declarations are properly placed on the Principal Display Panel (PDP)."
            )

        if product.isPDPPlacementValid is False:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.FAIL,
                severity=self.severity,
                message="Mandatory declarations are placed outside the statutory Principal Display Panel."
            )

        placement_text = (product.declarationPlacement or "").strip().upper()
        pdp_keywords = ["PDP", "FRONT", "PRINCIPAL", "PRINCIPAL DISPLAY PANEL", "MAIN PANEL"]

        if any(keyword in placement_text for keyword in pdp_keywords):
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.PASS,
                severity=self.severity,
                message=f"Declaration placement area '{product.declarationPlacement}' satisfies Principal Display Panel requirements."
            )

        return IndividualRuleResult(
            ruleId=self.rule_id,
            ruleName=self.rule_name,
            status=RuleStatus.MANUAL_REVIEW,
            severity=RuleSeverity.MEDIUM,
            message=f"Declaration placement location '{product.declarationPlacement}' requires manual label verification for PDP compliance."
        )
