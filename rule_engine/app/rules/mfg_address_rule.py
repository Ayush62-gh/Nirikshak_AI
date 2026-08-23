"""
Legal Metrology Compliance Rule: Manufacturer or Packer Address Declaration Rule.
Statutory Provision: Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011.
"""

from typing import Optional
from app.core.interface import AbstractRule
from app.models.product import EvaluateProductRequest
from app.models.rule_result import IndividualRuleResult, RuleStatus, RuleSeverity
from app.rules.base import RuleRegistry


@RuleRegistry.register
class ManufacturerAddressRule(AbstractRule):
    """
    Validates declaration of Manufacturer or Packer complete address.
    Legal Reference: Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011.
    """

    @property
    def rule_id(self) -> str:
        return "LM-RULE-MFGADDR-006"

    @property
    def rule_name(self) -> str:
        return "Manufacturer or Packer Address Declaration Check"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    @property
    def target_field(self) -> str:
        return "manufacturerAddress"

    @property
    def remediation_hint(self) -> Optional[str]:

        return "Declare complete address of Manufacturer/Packer (premises, city, state, pincode) on package label."

    def is_applicable(self, product: EvaluateProductRequest) -> bool:
        """
        Applicability Condition:
        - Applies to all domestic packaged commodities (isImported != True).
        - Applies if manufacturer/packer details are specified on imported packages.
        - Excluded (NOT_APPLICABLE) ONLY if explicitly imported AND no manufacturer/packer details specified.
        """
        if product.isImported is True:
            if not product.manufacturerName and not product.packerName and not product.manufacturerAddress:
                return False
        return True

    def validate(self, product: EvaluateProductRequest) -> IndividualRuleResult:
        # Case 1: Address is completely missing
        if not product.manufacturerAddress or not product.manufacturerAddress.strip():
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.FAIL,
                severity=self.severity,
                message="Manufacturer or Packer address declaration is completely missing from product payload."
            )

        addr_text = product.manufacturerAddress.strip()

        # Case 2: Structured address declaration present
        return IndividualRuleResult(
            ruleId=self.rule_id,
            ruleName=self.rule_name,
            status=RuleStatus.PASS,
            severity=self.severity,
            message="Manufacturer or Packer address text is present in structured payload."
        )

