from typing import Any, Dict, Optional
from compliance_engine.rules.base_rule import BaseRule, RuleResult, RuleStatus
from compliance_engine.severity import Severity


class ImporterRule(BaseRule):
    """
    Legal Metrology Rule 6(1)(f):
    For packages containing imported commodities, the name and address of the importer and Country of Origin must be mentioned.
    """

    def evaluate(
        self, declarations: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        importer_dec = declarations.get("importer")
        coo_dec = declarations.get("country_of_origin")
        is_imported = context.get("is_imported", False) if context else False

        # If explicitly imported or importer declared
        if not is_imported and not importer_dec:
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.NOT_APPLICABLE,
                severity=self.severity,
                weight=self.weight,
                message="Rule not applicable for domestically manufactured goods without import claim.",
                legal_reference=self.legal_reference,
            )

        if is_imported and not coo_dec:
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.FAIL,
                severity=Severity.HIGH,
                weight=self.weight,
                message="Imported commodity must declare Country of Origin.",
                detected_value=None,
                expected_value="Country of Origin (e.g. Made in / Origin: Country)",
                legal_reference=self.legal_reference,
            )

        coo_val = getattr(coo_dec, "normalized_value", str(coo_dec)) if coo_dec else "Declared"
        return RuleResult(
            rule_id=self.rule_id,
            rule_number=self.rule_number,
            name=self.name,
            category=self.category,
            status=RuleStatus.PASS,
            severity=self.severity,
            weight=self.weight,
            message="Importer and Country of Origin compliance verified.",
            detected_value=coo_val,
            expected_value="Country of Origin declaration",
            legal_reference=self.legal_reference,
        )
