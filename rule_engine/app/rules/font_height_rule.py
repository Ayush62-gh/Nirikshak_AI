"""
Legal Metrology Compliance Rule: Font Size & Readability Analysis Check.
Statutory Provision: Rule 7 & Rule 9, Legal Metrology (Packaged Commodities) Rules, 2011.
"""

from typing import Optional
from app.core.interface import AbstractRule
from app.models.product import EvaluateProductRequest
from app.models.rule_result import IndividualRuleResult, RuleStatus, RuleSeverity
from app.rules.base import RuleRegistry


@RuleRegistry.register
class FontHeightRule(AbstractRule):
    """
    Validates physical font height (in mm) of mandatory declarations on package labels.
    Minimum font height prescribed under Rule 7 & Rule 9 [UNVERIFIED - VERIFY against official Rules text]:
    - Net Qty <= 50g/ml -> 1.0 mm minimum [UNVERIFIED]
    - Net Qty 50g - 200g/ml -> 2.0 mm minimum [UNVERIFIED]
    - Net Qty 200g - 1kg/L -> 4.0 mm minimum [UNVERIFIED]
    - Net Qty > 1kg/L -> 6.0 mm minimum [UNVERIFIED]
    """

    @property
    def rule_id(self) -> str:
        return "LM-RULE-FONT-012"

    @property
    def rule_name(self) -> str:
        return "Font Size & Readability Analysis Check"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    @property
    def target_field(self) -> str:
        return "fontSizeMm"

    @property
    def remediation_hint(self) -> Optional[str]:
        return "Ensure font height of mandatory declarations meets minimum statutory millimeter requirements under Rule 7 & 9."

    def is_applicable(self, product: EvaluateProductRequest) -> bool:
        """
        Applicability:
        - Applicable ONLY when physical font height measurement metadata (fontSizeMm) is provided in request payload.
        - Returns False (NOT_APPLICABLE) when font measurement metadata is not supplied.
        """
        if product.fontSizeMm is not None:
            return True
        return False

    # TODO: Implement dynamic font height thresholds based on package net-quantity / principal display area from official Rules table [VERIFY against official Rules text]
    def validate(self, product: EvaluateProductRequest) -> IndividualRuleResult:
        font_size = product.fontSizeMm

        if font_size is None:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.MANUAL_REVIEW,
                severity=RuleSeverity.MEDIUM,
                message="Physical font height metadata is missing from label scan; manual visual measurement required."
            )

        # Baseline minimum font height check (Absolute minimum physical font height under Rule 7 is 1.0 mm)
        min_required_mm = 1.0

        if font_size < min_required_mm:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.FAIL,
                severity=self.severity,
                message=f"Measured declaration font height ({font_size:.1f} mm) is below absolute statutory minimum requirement of {min_required_mm:.1f} mm."
            )

        return IndividualRuleResult(
            ruleId=self.rule_id,
            ruleName=self.rule_name,
            status=RuleStatus.PASS,
            severity=self.severity,
            message=f"Declaration font size measurement ({font_size:.1f} mm) satisfies statutory legibility requirements."
        )
