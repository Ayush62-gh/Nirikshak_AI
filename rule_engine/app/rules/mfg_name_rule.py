"""
Legal Metrology Compliance Rule: Manufacturer or Packer Name Declaration Rule.
Statutory Provision: Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011.
"""

from typing import Optional
from app.core.interface import AbstractRule
from app.models.product import EvaluateProductRequest
from app.models.rule_result import IndividualRuleResult, RuleStatus, RuleSeverity
from app.rules.base import RuleRegistry


@RuleRegistry.register
class ManufacturerNameRule(AbstractRule):
    """
    Validates declaration of Manufacturer or Packer Name.
    Legal Reference: Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011.
    """

    @property
    def rule_id(self) -> str:
        return "LM-RULE-MFGNAME-005"

    @property
    def rule_name(self) -> str:
        return "Manufacturer or Packer Name Declaration Check"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.CRITICAL

    @property
    def target_field(self) -> str:
        return "manufacturerName"

    @property
    def remediation_hint(self) -> Optional[str]:

        return "Declare the name of the Manufacturer or Packer clearly on the package label."

    def is_applicable(self, product: EvaluateProductRequest) -> bool:
        """
        Applicability Condition:
        - Applies to all domestic packaged commodities (isImported != True).
        - Applies if manufacturer/packer details are explicitly specified on imported packages.
        - Excluded (NOT_APPLICABLE) ONLY if explicitly imported AND no manufacturer details specified (handled by Importer rule).
        """
        if product.isImported is True:
            if not product.manufacturerName and not product.packerName:
                return False
        return True

    def validate(self, product: EvaluateProductRequest) -> IndividualRuleResult:
        mfg_name = product.manufacturerName.strip() if product.manufacturerName else None
        packer_name = product.packerName.strip() if product.packerName else None

        # Case 1: Both Manufacturer Name and Packer Name are completely missing
        if not mfg_name and not packer_name:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.FAIL,
                severity=self.severity,
                message="Name of Manufacturer or Packer is completely missing from product payload."
            )

        # Case 2: Structured declaration present
        return IndividualRuleResult(
            ruleId=self.rule_id,
            ruleName=self.rule_name,
            status=RuleStatus.PASS,
            severity=self.severity,
            message="Manufacturer or Packer name declaration is present in structured payload."
        )

