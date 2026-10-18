"""
Legal Metrology Compliance Rule: Physical Legibility & Color Contrast Rule.
Statutory Provision: Rule 8 [VERIFY against official Rules text], Legal Metrology (Packaged Commodities) Rules, 2011.
"""

from typing import Optional
from app.core.interface import AbstractRule
from app.models.product import EvaluateProductRequest
from app.models.rule_result import IndividualRuleResult, RuleStatus, RuleSeverity
from app.rules.base import RuleRegistry


@RuleRegistry.register
class ReadabilityContrastRule(AbstractRule):
    """
    Validates physical legibility and visual contrast of mandatory declarations.
    Legal Reference: Rule 8, Legal Metrology (Packaged Commodities) Rules, 2011.
    """

    @property
    def rule_id(self) -> str:
        return "LM-RULE-READ-014"

    @property
    def rule_name(self) -> str:
        return "Physical Legibility & Color Contrast Check"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.HIGH

    @property
    def target_field(self) -> str:
        return "contrastRatio"

    @property
    def remediation_hint(self) -> Optional[str]:
        return "Ensure label text has adequate color contrast against background packaging for legibility under Rule 8."

    def is_applicable(self, product: EvaluateProductRequest) -> bool:
        """
        Applicability:
        - Applicable when contrastRatio numeric measurement OR isLegible boolean is supplied in request payload.
        - Returns False (NOT_APPLICABLE) when visual contrast metadata is not provided.
        """
        if product.contrastRatio is not None:
            return True
        if product.isLegible is not None:
            return True
        return False

    def validate(self, product: EvaluateProductRequest) -> IndividualRuleResult:
        if product.isLegible is False:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.FAIL,
                severity=self.severity,
                message="Label text legibility does not meet statutory standards under Rule 8."
            )

        if product.contrastRatio is not None:
            if product.contrastRatio >= 4.5:
                return IndividualRuleResult(
                    ruleId=self.rule_id,
                    ruleName=self.rule_name,
                    status=RuleStatus.PASS,
                    severity=self.severity,
                    message=f"Text contrast ratio ({product.contrastRatio}:1) meets statutory legibility standards."
                )
            elif product.contrastRatio < 3.0:
                return IndividualRuleResult(
                    ruleId=self.rule_id,
                    ruleName=self.rule_name,
                    status=RuleStatus.FAIL,
                    severity=self.severity,
                    message=f"Text contrast ratio ({product.contrastRatio}:1) is insufficient for legibility under Rule 8."
                )
            else:
                return IndividualRuleResult(
                    ruleId=self.rule_id,
                    ruleName=self.rule_name,
                    status=RuleStatus.MANUAL_REVIEW,
                    severity=RuleSeverity.MEDIUM,
                    message=f"Text contrast ratio ({product.contrastRatio}:1) requires manual verification."
                )

        if product.isLegible is True:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.PASS,
                severity=self.severity,
                message="Visual legibility and contrast meet statutory standards."
            )

        return IndividualRuleResult(
            ruleId=self.rule_id,
            ruleName=self.rule_name,
            status=RuleStatus.MANUAL_REVIEW,
            severity=RuleSeverity.MEDIUM,
            message="Visual legibility and color contrast require label verification."
        )
