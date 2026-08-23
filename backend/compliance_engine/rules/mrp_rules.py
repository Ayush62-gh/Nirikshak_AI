from typing import Any, Dict, Optional
from compliance_engine.rules.base_rule import BaseRule, RuleResult, RuleStatus
from compliance_engine.severity import Severity
from app.utils.validators import has_tax_inclusive_declaration


class MRPRule(BaseRule):
    """
    Legal Metrology Rule 6(1)(e):
    Every package shall bear Maximum Retail Price (MRP) inclusive of all taxes.
    """

    def evaluate(
        self, declarations: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        mrp_dec = declarations.get("mrp")

        if not mrp_dec:
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.FAIL,
                severity=self.severity,
                weight=self.weight,
                message="Mandatory Maximum Retail Price (MRP) declaration is missing on the package.",
                detected_value=None,
                expected_value="MRP Rs. XX.XX (incl. of all taxes)",
                legal_reference=self.legal_reference,
            )

        extracted_val = getattr(mrp_dec, "extracted_value", str(mrp_dec))
        norm_val = getattr(mrp_dec, "normalized_value", extracted_val)
        source_img = getattr(mrp_dec, "source_image", None)

        has_taxes = has_tax_inclusive_declaration(extracted_val)
        is_valid = getattr(mrp_dec, "is_valid", has_taxes)

        if not has_taxes:
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.FAIL,
                severity=Severity.HIGH,
                weight=self.weight,
                message="MRP declaration is present but missing the mandatory 'inclusive of all taxes' clause.",
                detected_value=extracted_val,
                expected_value="MRP declaration with 'incl. of all taxes' or 'inclusive of all taxes'",
                legal_reference=self.legal_reference,
                evidence_image=source_img,
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_number=self.rule_number,
            name=self.name,
            category=self.category,
            status=RuleStatus.PASS,
            severity=self.severity,
            weight=self.weight,
            message="Valid MRP declared inclusive of all taxes.",
            detected_value=norm_val,
            expected_value="Valid MRP with taxes included",
            legal_reference=self.legal_reference,
            evidence_image=source_img,
        )
