"""
Legal Metrology Compliance Rule: Month and Year of Packing / Manufacture Rule.
Statutory Provision: Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011.
"""

from typing import Optional
from app.core.interface import AbstractRule
from app.models.product import EvaluateProductRequest
from app.models.rule_result import IndividualRuleResult, RuleStatus, RuleSeverity
from app.rules.base import RuleRegistry


@RuleRegistry.register
class DateOfPackingRule(AbstractRule):
    """
    Validates Month and Year of packing or manufacture declaration.
    Legal Reference: Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011.
    """

    @property
    def rule_id(self) -> str:
        return "LM-RULE-DATE-007"

    @property
    def rule_name(self) -> str:
        return "Month and Year of Packing / Manufacture Check"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    @property
    def target_field(self) -> str:
        return "monthOfPacking"

    @property
    def remediation_hint(self) -> Optional[str]:

        return "Declare Month and Year of packing/manufacture in standard format (e.g., '07/2026' or 'July 2026')."

    def is_applicable(self, product: EvaluateProductRequest) -> bool:
        """Month and Year declaration applies to all packaged commodities."""
        return True

    def validate(self, product: EvaluateProductRequest) -> IndividualRuleResult:
        month = product.monthOfPacking.strip() if product.monthOfPacking else None
        year = product.yearOfPacking.strip() if product.yearOfPacking else None

        # Case 1: Both month and year are completely missing
        if not month and not year:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.FAIL,
                severity=self.severity,
                message="Month and Year of packing or manufacture is completely missing."
            )

        # Case 2: Only one of month or year is present
        if not month or not year:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.FAIL,
                severity=self.severity,
                message="Incomplete date declaration; both Month AND Year of packing/manufacture are required."
            )

        # Case 3: Verify month and year formats
        valid_months = {
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
            "01", "02", "03", "04", "05", "06", "07", "08", "09",
            "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
            "january", "february", "march", "april", "june", "july", "august", "september", "october", "november", "december"
        }

        m_clean = month.lower()
        if m_clean not in valid_months:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.MANUAL_REVIEW,
                severity=RuleSeverity.MEDIUM,
                message=f"Month value '{month}' is non-standard; manual label verification required."
            )

        # Validate year length/digits
        if not year.isdigit() or len(year) not in (2, 4):
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.MANUAL_REVIEW,
                severity=RuleSeverity.MEDIUM,
                message=f"Year value '{year}' is non-standard; manual label verification required."
            )

        # Case 4: Complete valid month and year declared
        return IndividualRuleResult(
            ruleId=self.rule_id,
            ruleName=self.rule_name,
            status=RuleStatus.PASS,
            severity=self.severity,
            message="Month and Year of packing/manufacture declaration is present in standard format."
        )
