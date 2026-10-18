"""
Legal Metrology Compliance Rule: Manufacturer or Packer Address Declaration Rule.
Statutory Provision: Rule 6(1)(a) [VERIFY against official Rules text], Legal Metrology (Packaged Commodities) Rules, 2011.
"""

import re
from typing import Optional
from app.core.interface import AbstractRule
from app.models.product import EvaluateProductRequest
from app.models.rule_result import IndividualRuleResult, RuleStatus, RuleSeverity
from app.rules.base import RuleRegistry


@RuleRegistry.register
class ManufacturerAddressRule(AbstractRule):
    """
    Validates declaration of Manufacturer or Packer complete address.
    Legal Reference: Rule 6(1)(a) [VERIFY against official Rules text], Legal Metrology (Packaged Commodities) Rules, 2011.
    
    Known Limitation: 6-digit numbers in address text (such as batch or licence numbers) may be incorrectly matched as postal pincodes.
    """

    # Indian 6-digit postal pincode pattern (supports optional space, e.g. "201301" or "400 001")
    PINCODE_PATTERN = re.compile(r'\b[1-9]\d{2}\s?\d{3}\b')

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
        return "Declare complete address of Manufacturer/Packer (premises, city, state, 6-digit pincode) on package label."

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

        # Case 2: Check 6-digit pincode in address
        if self.PINCODE_PATTERN.search(addr_text):
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.PASS,
                severity=self.severity,
                message="Manufacturer or Packer address text is present with 6-digit pincode."
            )

        # Case 3: Address present but missing 6-digit pincode -> MANUAL_REVIEW
        return IndividualRuleResult(
            ruleId=self.rule_id,
            ruleName=self.rule_name,
            status=RuleStatus.MANUAL_REVIEW,
            severity=RuleSeverity.MEDIUM,
            message="Manufacturer or Packer address text is present, but missing 6-digit pincode; manual verification required."
        )

