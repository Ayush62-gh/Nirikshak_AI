"""
Legal Metrology Compliance Rule: Unit Sale Price (USP) Declaration Check.
Statutory Provision: Rule 6(11), Legal Metrology (Packaged Commodities) Rules, 2011 (2021 DoCA Amendment).
"""

import re
from typing import Optional
from app.core.interface import AbstractRule
from app.models.product import EvaluateProductRequest
from app.models.rule_result import IndividualRuleResult, RuleStatus, RuleSeverity
from app.rules.base import RuleRegistry


@RuleRegistry.register
class UnitSalePriceRule(AbstractRule):
    """
    Validates Unit Sale Price (USP) declaration on retail packaged commodities.
    Mandatory for packages containing > 1 g/ml or > 1 unit as per Rule 6(11).
    """

    # TEMPORARY CONSERVATIVE CHOICE: Missing USP on packages with netQuantity present defaults to MANUAL_REVIEW
    # until the exact statutory applicability conditions and threshold logic under Rule 6(11) are officially verified.
    MISSING_USP_DEFAULT_STATUS = RuleStatus.MANUAL_REVIEW

    # Patterns matching Unit Sale Price declarations (e.g., "Rs 0.50/g", "Rs. 200 / kg", "₹1.50/ml", "₹10 per N", "Unit Price: Rs 5.00/g")
    USP_PATTERNS = [
        re.compile(r'(?:₹|rs\.?|inr)\s*\d+(?:\.\d+)?\s*(?:/|per)\s*(?:g|gram|kg|kilogram|ml|l|liter|litre|m|cm|n|unit|piece)', re.IGNORECASE),
        re.compile(r'unit\s*(?:sale\s*)?price\s*:?\s*(?:₹|rs\.?|inr)?\s*\d+', re.IGNORECASE),
    ]

    @property
    def rule_id(self) -> str:
        return "LM-RULE-USP-010"

    @property
    def rule_name(self) -> str:
        return "Unit Sale Price (USP) Declaration Check"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    @property
    def target_field(self) -> str:
        return "unitSalePrice"

    @property
    def remediation_hint(self) -> Optional[str]:
        return "Declare Unit Sale Price in standard format (e.g. 'Rs. 0.50 / g' or '₹200.00 / kg') alongside MRP on package labels."

    def _has_usp_in_mrp(self, mrp_text: str) -> bool:
        if not mrp_text:
            return False
        return any(pattern.search(mrp_text) for pattern in self.USP_PATTERNS)

    def is_applicable(self, product: EvaluateProductRequest) -> bool:
        """
        Applicability:
        - Applicable if unitSalePrice is provided OR if USP pattern is detected inside mrp.
        - Applicable if netQuantity is provided with numeric quantity (package potentially requiring USP under Rule 6(11)).
        - Returns False (NOT_APPLICABLE) when neither USP nor netQuantity is supplied in request payload.
        """
        if product.unitSalePrice and product.unitSalePrice.strip():
            return True
        if product.mrp and self._has_usp_in_mrp(product.mrp):
            return True
        if product.netQuantity and re.search(r'\d', product.netQuantity):
            return True
        return False

    def validate(self, product: EvaluateProductRequest) -> IndividualRuleResult:
        usp_field = (product.unitSalePrice or "").strip()
        mrp_text = (product.mrp or "").strip()

        # Check explicit unitSalePrice field first
        if usp_field:
            for pattern in self.USP_PATTERNS:
                if pattern.search(usp_field):
                    return IndividualRuleResult(
                        ruleId=self.rule_id,
                        ruleName=self.rule_name,
                        status=RuleStatus.PASS,
                        severity=self.severity,
                        message=f"Unit Sale Price declaration is present: '{usp_field}'."
                    )
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.MANUAL_REVIEW,
                severity=RuleSeverity.MEDIUM,
                message=f"Unit Sale Price text '{usp_field}' is non-standard; manual label verification required."
            )

        # Check if USP is embedded inside MRP text snippet
        if mrp_text:
            for pattern in self.USP_PATTERNS:
                match = pattern.search(mrp_text)
                if match:
                    return IndividualRuleResult(
                        ruleId=self.rule_id,
                        ruleName=self.rule_name,
                        status=RuleStatus.PASS,
                        severity=self.severity,
                        message=f"Unit Sale Price detected in price snippet: '{match.group(0)}'."
                    )

        # USP is missing, but netQuantity is present.
        # TODO: Verify exact Rule 6(11) statutory mandatory thresholds (packages > 1g/1ml or > 1 unit) [VERIFY against official Rules text]
        if product.netQuantity and product.netQuantity.strip():
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=self.MISSING_USP_DEFAULT_STATUS,
                severity=RuleSeverity.MEDIUM,
                message="Unit Sale Price declaration is missing; manual verification required to check applicability under Rule 6(11)."
            )

        # Defensive fallback: unreachable via engine since is_applicable() returns False in this case.
        return IndividualRuleResult(
            ruleId=self.rule_id,
            ruleName=self.rule_name,
            status=self.MISSING_USP_DEFAULT_STATUS,
            severity=RuleSeverity.LOW,
            message="Unit Sale Price declaration is missing and net quantity is unprovided."
        )
