"""
Legal Metrology Compliance Rule: Best Before / Expiry Date Declaration Check.
Statutory Provision: Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011 & FSSAI Packaging Guidelines.
"""

import re
from typing import Optional
from app.core.interface import AbstractRule
from app.models.product import EvaluateProductRequest
from app.models.rule_result import IndividualRuleResult, RuleStatus, RuleSeverity
from app.rules.base import RuleRegistry


@RuleRegistry.register
class ExpiryDateRule(AbstractRule):
    """
    Validates Best Before / Expiry Date declaration on perishable, food, cosmetic, and drug commodities.
    """

    EXPIRY_PATTERNS = [
        re.compile(r'\bbest\s*before\s*:?\s*\d+\s*(?:months?|years?|days?)\b', re.IGNORECASE),
        re.compile(r'\bexp(?:iry)?\s*(?:date)?\s*:?\s*(?:0?[1-9]|1[0-2])[/\.-]\d{2,4}\b', re.IGNORECASE),
        re.compile(r'\buse\s*by\s*:?\s*(?:0?[1-9]|1[0-2])[/\.-]\d{2,4}\b', re.IGNORECASE),
        re.compile(r'\b(?:0?[1-9]|1[0-2])[/\.-](?:20\d{2}|\d{4})\b', re.IGNORECASE),
    ]

    PERISHABLE_TYPES = {"food", "cosmetics", "pharma", "pharmaceuticals", "drug", "drugs", "beverage", "beverages"}

    @property
    def rule_id(self) -> str:
        return "LM-RULE-EXP-011"

    @property
    def rule_name(self) -> str:
        return "Best Before / Expiry Date Declaration Check"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    @property
    def target_field(self) -> str:
        return "expiryDate"

    @property
    def remediation_hint(self) -> Optional[str]:
        return "Declare 'Best Before' period or 'Expiry Date' (e.g. 'Best Before 12 Months from Mfd' or 'Exp: 12/2027') on perishable package labels."

    def is_applicable(self, product: EvaluateProductRequest) -> bool:
        """
        Applicability Condition:
        - Applicable if productType is explicitly in PERISHABLE_TYPES OR if expiryDate is provided.
        - Returns False (NOT_APPLICABLE) for unprovided expiry date on general/unconfirmed product categories.
        """
        ptype = (product.productType or "").strip().lower()
        if ptype in self.PERISHABLE_TYPES or (product.expiryDate and product.expiryDate.strip()):
            return True
        return False

    def validate(self, product: EvaluateProductRequest) -> IndividualRuleResult:
        expiry_val = (product.expiryDate or "").strip()

        if expiry_val:
            for pattern in self.EXPIRY_PATTERNS:
                if pattern.search(expiry_val):
                    return IndividualRuleResult(
                        ruleId=self.rule_id,
                        ruleName=self.rule_name,
                        status=RuleStatus.PASS,
                        severity=self.severity,
                        message=f"Expiry / Best Before declaration is present: '{expiry_val}'."
                    )
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.MANUAL_REVIEW,
                severity=RuleSeverity.MEDIUM,
                message=f"Expiry / Best Before text '{expiry_val}' is non-standard; manual label verification required."
            )

        ptype = (product.productType or "").strip().lower()

        # If perishable product lacks expiry date declaration
        if ptype in self.PERISHABLE_TYPES:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.FAIL,
                severity=self.severity,
                message=f"Mandatory Best Before / Expiry Date declaration is missing for perishable category '{product.productType}'."
            )

        if ptype:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.NOT_APPLICABLE,
                severity=self.severity,
                message="Expiry date declaration is not mandatory for non-perishable commodity."
            )

        return IndividualRuleResult(
            ruleId=self.rule_id,
            ruleName=self.rule_name,
            status=RuleStatus.MANUAL_REVIEW,
            severity=RuleSeverity.MEDIUM,
            message="Expiry date declaration is not present; verify if commodity is non-perishable."
        )
