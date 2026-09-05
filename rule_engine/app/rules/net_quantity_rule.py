"""
Legal Metrology Compliance Rule: Net Quantity Declaration Rule.
Statutory Provision: Rule 6(1)(c), Rule 11 & Rule 12, Legal Metrology (Packaged Commodities) Rules, 2011.
"""

import re
from typing import Optional
from app.core.interface import AbstractRule
from app.models.product import EvaluateProductRequest
from app.models.rule_result import IndividualRuleResult, RuleStatus, RuleSeverity
from app.rules.base import RuleRegistry


@RuleRegistry.register
class NetQuantityRule(AbstractRule):
    """
    Validates Net Quantity declaration presence and standard metric unit categorization (Weight, Volume, Length, Area, Number).
    Legal Reference: Rule 6(1)(c), Rule 11 & Rule 12, Legal Metrology (Packaged Commodities) Rules, 2011.
    """

    @property
    def rule_id(self) -> str:
        return "LM-RULE-NETQTY-002"

    @property
    def rule_name(self) -> str:
        return "Net Quantity Declaration Check"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    @property
    def target_field(self) -> str:
        return "netQuantity"

    @property
    def remediation_hint(self) -> Optional[str]:

        return "Declare Net Quantity in standard metric units (Weight: g/kg, Volume: ml/L, Length: m/cm, Area: sq m, Number: N/count)."

    def is_applicable(self, product: EvaluateProductRequest) -> bool:
        """Net quantity declaration applies to all packaged commodities."""
        return True

    def _determine_quantity_category(self, text: str) -> Optional[str]:
        """Categorizes net quantity unit into WEIGHT, VOLUME, LENGTH, AREA, or NUMBER_OR_UNIT."""
        if re.search(r'\b(sq m|sq cm|sq meter|square meter)\b', text, re.IGNORECASE):
            return "AREA"
        if re.search(r'\b(g|gram|grams|kg|kilogram|kilograms|mg|milligram)\b', text, re.IGNORECASE):
            return "WEIGHT"
        if re.search(r'\b(ml|milliliter|millilitres|l|liter|liters|litre|litres|cl)\b', text, re.IGNORECASE):
            return "VOLUME"
        if re.search(r'\b(m|meter|meters|cm|centimeter|mm|millimeter)\b', text, re.IGNORECASE):
            return "LENGTH"
        if re.search(r'\b(n|units|pcs|pieces|count|items|no|number)\b', text, re.IGNORECASE):
            return "NUMBER_OR_UNIT"
        return None


    def validate(self, product: EvaluateProductRequest) -> IndividualRuleResult:
        # Step 1: Check presence
        if not product.netQuantity or not product.netQuantity.strip():
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.FAIL,
                severity=self.severity,
                message="Net Quantity declaration is completely missing from product payload."
            )

        qty_text = product.netQuantity.strip().lower()
        has_digits = any(c.isdigit() for c in qty_text)

        if not has_digits:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.FAIL,
                severity=self.severity,
                message="Net Quantity declaration lacks a valid numeric quantity value."
            )

        # Step 2: Categorize unit type
        category = self._determine_quantity_category(qty_text)

        # Clear PASS: Contains numeric value AND recognizable statutory metric unit category
        if category:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.PASS,
                severity=self.severity,
                message=f"Net Quantity declaration is present in valid statutory metric units (Category: {category})."
            )

        # MANUAL_REVIEW: Numeric value present, but unit cannot be categorized or requires physical label/category verification
        return IndividualRuleResult(
            ruleId=self.rule_id,
            ruleName=self.rule_name,
            status=RuleStatus.MANUAL_REVIEW,
            severity=RuleSeverity.MEDIUM,
            message="Net Quantity numeric value present, but unit category alignment requires physical label verification."
        )



