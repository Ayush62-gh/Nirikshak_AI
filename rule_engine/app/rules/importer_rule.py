"""
Legal Metrology Compliance Rule: Importer Declaration Rule for Foreign Commodities.
Statutory Provision: Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011.
"""

from typing import Optional
from app.core.interface import AbstractRule
from app.models.product import EvaluateProductRequest
from app.models.rule_result import IndividualRuleResult, RuleStatus, RuleSeverity
from app.rules.base import RuleRegistry


@RuleRegistry.register
class ImporterDeclarationRule(AbstractRule):
    """
    Validates Importer Name and Address declaration on imported packaged commodities.
    Legal Reference: Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011.
    """

    @property
    def rule_id(self) -> str:
        return "LM-RULE-IMP-003"

    @property
    def rule_name(self) -> str:
        return "Importer Name & Address Check for Foreign Commodities"

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.CRITICAL

    @property
    def target_field(self) -> str:
        return "importerName"

    @property
    def remediation_hint(self) -> Optional[str]:

        return "Declare name and complete Indian office address of the Importer on imported package labels."

    def is_applicable(self, product: EvaluateProductRequest) -> bool:
        """
        Applicability Condition:
        - Evaluated directly against product.isImported flag.
        - Returns False (NOT_APPLICABLE) ONLY if explicitly flagged as non-imported (isImported == False).
        """
        if product.isImported is False:
            return False
        return True

    def validate(self, product: EvaluateProductRequest) -> IndividualRuleResult:
        # Case 1: Import status is unconfirmed (isImported is None)
        if product.isImported is None:
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.MANUAL_REVIEW,
                severity=RuleSeverity.MEDIUM,
                message="Import status is unconfirmed in structured payload; manual review required to determine if commodity is imported."
            )

        # Case 2: Confirmed imported commodity, but importer name/details are missing
        if not product.importerName or not product.importerName.strip():
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.FAIL,
                severity=self.severity,
                message="Mandatory Importer name and address declaration is missing on imported package."
            )

        # Case 3: Importer name is declared
        return IndividualRuleResult(
            ruleId=self.rule_id,
            ruleName=self.rule_name,
            status=RuleStatus.PASS,
            severity=self.severity,
            message="Importer declaration is present on imported package."
        )


