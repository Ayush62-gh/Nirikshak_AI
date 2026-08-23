"""
Rule Interface contract for Legal Metrology Rules.
"""

from abc import ABC, abstractmethod
from typing import Optional
from app.models.product import EvaluateProductRequest
from app.models.rule_result import IndividualRuleResult, RuleStatus, RuleSeverity, RuleEvidence, EvidenceSource


class AbstractRule(ABC):
    """
    Abstract Base Class defining the contract for every Legal Metrology Compliance Rule.
    All individual rule implementations inherit from this class.
    """

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique ID identifier for the rule (e.g., 'LM-RULE-MRP-001')."""
        pass

    @property
    @abstractmethod
    def rule_name(self) -> str:
        """Human-readable name of the rule."""
        pass

    @property
    def severity(self) -> RuleSeverity:
        """Severity level associated with rule failure (Default: HIGH)."""
        return RuleSeverity.HIGH

    @property
    def target_field(self) -> Optional[str]:
        """Target product request field evaluated by this rule."""
        return None

    @property
    def remediation_hint(self) -> Optional[str]:
        """Default suggested remediation for violations of this rule."""
        return None

    def is_applicable(self, product: EvaluateProductRequest) -> bool:
        """
        Determines whether this rule applies to the provided product payload.
        Override in subclasses for condition-based rules (e.g. import-only rules).
        Default returns True.
        """
        return True

    @abstractmethod
    def validate(self, product: EvaluateProductRequest) -> IndividualRuleResult:
        """
        Executes core validation logic when rule is applicable.
        Must return an IndividualRuleResult with status PASS, FAIL, or MANUAL_REVIEW.
        """
        pass

    def evaluate(self, product: EvaluateProductRequest) -> IndividualRuleResult:
        """
        Generic rule execution template method:
        1. Resolves evidence provenance from product input or constructs structured evidence.
        2. Checks applicability via is_applicable(product).
        3. Returns NOT_APPLICABLE status if condition is not met.
        4. Invokes validate(product) if rule applies.
        5. Binds target field and evidence provenance to result schema.
        """
        field_name = self.target_field or "general"
        provided_evidence = product.fieldEvidence.get(field_name) if product.fieldEvidence else None

        if provided_evidence is not None:
            evidence = provided_evidence
        else:
            field_val = getattr(product, field_name, None) if self.target_field else None
            evidence = RuleEvidence(
                field=field_name,
                value=field_val,
                source=EvidenceSource.STRUCTURED_INPUT,
                confidence=1.0
            )

        if not self.is_applicable(product):
            return IndividualRuleResult(
                ruleId=self.rule_id,
                ruleName=self.rule_name,
                status=RuleStatus.NOT_APPLICABLE,
                severity=self.severity,
                message=f"Rule '{self.rule_id}' is not applicable for this product configuration.",
                field=field_name,
                evidence=evidence
            )

        res = self.validate(product)
        if res.field is None:
            res.field = field_name
        if res.evidence is None:
            res.evidence = evidence
        return res



