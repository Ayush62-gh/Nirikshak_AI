from typing import Any, Dict, Optional
from compliance_engine.rules.base_rule import BaseRule, RuleResult, RuleStatus
from compliance_engine.severity import Severity
from app.utils.validators import is_legal_unit


class NetQuantityRule(BaseRule):
    """
    Legal Metrology Rule 6(1)(c) and Rule 13:
    Every package must declare Net Quantity in standard units of weight, measure, or number.
    """

    def evaluate(
        self, declarations: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        qty_dec = declarations.get("net_quantity")

        if not qty_dec:
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.FAIL,
                severity=self.severity,
                weight=self.weight,
                message="Mandatory Net Quantity declaration is missing on the package.",
                detected_value=None,
                expected_value="Net Qty in standard units (e.g. g, kg, ml, l, N, U)",
                legal_reference=self.legal_reference,
            )

        extracted_val = getattr(qty_dec, "extracted_value", str(qty_dec))
        norm_val = getattr(qty_dec, "normalized_value", extracted_val)
        source_img = getattr(qty_dec, "source_image", None)
        is_valid = getattr(qty_dec, "is_valid", True)

        # Extract unit from normalized value
        parts = norm_val.split()
        unit = parts[-1] if len(parts) > 1 else ""

        if not is_legal_unit(unit):
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.WARNING,
                severity=Severity.MEDIUM,
                weight=self.weight,
                message=f"Net quantity unit '{unit}' is non-standard under Rule 13 standard units.",
                detected_value=extracted_val,
                expected_value="Standard SI unit: g, kg, ml, l, m, cm, mm, N, U",
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
            message="Net Quantity declared in compliance with standard units.",
            detected_value=norm_val,
            expected_value="Standard Net Quantity declaration",
            legal_reference=self.legal_reference,
            evidence_image=source_img,
        )
