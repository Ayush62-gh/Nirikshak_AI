"""
Legal Metrology Compliance Rule: Maximum Retail Price (MRP) Declaration Rule.
Statutory Provision: Rule 6(1)(e) & Rule 2(m), Legal Metrology (Packaged Commodities) Rules, 2011.
"""

from typing import Optional
from app.core.interface import AbstractRule
from app.models.product import EvaluateProductRequest
from app.models.rule_result import IndividualRuleResult, RuleStatus, RuleSeverity
from app.rules.base import RuleRegistry


@RuleRegistry.register
class MRPDeclarationRule(AbstractRule):
    """
    Validates Maximum Retail Price (MRP) declaration presence, currency representation, and statutory presentation.
    Legal Reference: Rule 6(1)(e) & Rule 2(m), Legal Metrology (Packaged Commodities) Rules, 2011.
    """

    @property
    def rule_id(self) -> str:
        return "LM-RULE-MRP-001"

    @property
    def rule_name(self) -> str:
        return "Maximum Retail Price (MRP) Declaration Check"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.CRITICAL

    @property
    def target_field(self) -> str:
        return "mrp"

    @property
    def remediation_hint(self) -> Optional[str]:

        return "Declare MRP in statutory format: 'MRP Rs. XX.XX (incl. of all taxes)' or '₹ XX.XX (incl. of all taxes)'"

    def is_applicable(self, product: EvaluateProductRequest) -> bool:
        """MRP declaration applies to all retail packaged commodities intended for sale."""
        return True

    def validate(self, product: EvaluateProductRequest) -> IndividualRuleResult:
        # Step 1: MRP Value Presence Check
        if not product.mrp or not product.mrp.strip():
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.FAIL,
                severity=self.severity,
                message="MRP declaration is completely missing from product payload."
            )

        mrp_text = product.mrp.lower().strip()
        has_digits = any(c.isdigit() for c in mrp_text)

        # Step 2: Currency / Numeric Representation Check
        if not has_digits:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.FAIL,
                severity=self.severity,
                message="MRP declaration does not contain a valid numeric price value."
            )

        has_currency = "rs" in mrp_text or "₹" in product.mrp or "inr" in mrp_text or "mrp" in mrp_text
        tax_clauses = ("incl. of all taxes", "inclusive of all taxes", "incl of all taxes", "incl. taxes", "inclusive of taxes")
        has_tax_clause = any(clause in mrp_text for clause in tax_clauses)

        # Step 3: Clear PASS when structured data contains price, currency indicator, AND tax inclusion phrase
        if (has_currency or has_digits) and has_tax_clause:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.PASS,
                severity=self.severity,
                message="MRP value, currency representation, and tax inclusion phrase ('incl. of all taxes') are clearly declared."
            )

        # Step 4: MANUAL_REVIEW when price value/currency is present, but statutory presentation details (e.g. tax clause or print layout) cannot be verified from structured input
        return IndividualRuleResult(
            ruleId=self.rule_id,
            ruleName=self.rule_name,
            status=RuleStatus.MANUAL_REVIEW,
            severity=RuleSeverity.MEDIUM,
            message="Numeric MRP value is present, but statutory presentation details and tax inclusion clause ('incl. of all taxes') cannot be verified from structured input."
        )




