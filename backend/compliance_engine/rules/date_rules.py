from typing import Any, Dict, Optional
from compliance_engine.rules.base_rule import BaseRule, RuleResult, RuleStatus
from compliance_engine.severity import Severity
from app.utils.validators import DATE_PATTERN


class DateDeclarationRule(BaseRule):
    """
    Legal Metrology Rule 6(1)(d):
    Month and Year of manufacture, pre-packing, or import must be declared on the package.
    """

    def evaluate(
        self, declarations: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        # Check either mfg_date or pkd_date
        mfg_dec = declarations.get("mfg_date") or declarations.get("pkd_date")

        if not mfg_dec:
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.FAIL,
                severity=self.severity,
                weight=self.weight,
                message="Mandatory Month and Year of Manufacture / Packaging date declaration is missing.",
                detected_value=None,
                expected_value="Month & Year (e.g. MM/YYYY or MM/YY or DD/MM/YYYY)",
                legal_reference=self.legal_reference,
            )

        extracted_val = getattr(mfg_dec, "extracted_value", str(mfg_dec))
        norm_val = getattr(mfg_dec, "normalized_value", extracted_val)
        source_img = getattr(mfg_dec, "source_image", None)

        if not DATE_PATTERN.search(norm_val) and not DATE_PATTERN.search(extracted_val):
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.WARNING,
                severity=Severity.MEDIUM,
                weight=self.weight,
                message=f"Date format '{extracted_val}' may not clearly identify month and year.",
                detected_value=extracted_val,
                expected_value="Standard Month/Year format (e.g. MM/YYYY)",
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
            message="Valid manufacturing/packaging date declared.",
            detected_value=norm_val,
            expected_value="Valid Month and Year declaration",
            legal_reference=self.legal_reference,
            evidence_image=source_img,
        )
