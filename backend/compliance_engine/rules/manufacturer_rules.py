from typing import Any, Dict, Optional
from compliance_engine.rules.base_rule import BaseRule, RuleResult, RuleStatus
from compliance_engine.severity import Severity
from app.utils.validators import is_valid_pincode


class ManufacturerRule(BaseRule):
    """
    Legal Metrology Rule 6(1)(a):
    The name and complete address of the manufacturer or packer, including PIN code, shall be declared.
    """

    def evaluate(
        self, declarations: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        mfg_dec = declarations.get("manufacturer") or declarations.get("packer")

        if not mfg_dec:
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.FAIL,
                severity=self.severity,
                weight=self.weight,
                message="Manufacturer / Packer name and address declaration is missing.",
                detected_value=None,
                expected_value="Complete manufacturer/packer name, registered address with PIN code",
                legal_reference=self.legal_reference,
            )

        extracted_val = getattr(mfg_dec, "extracted_value", str(mfg_dec))
        norm_val = getattr(mfg_dec, "normalized_value", extracted_val)
        source_img = getattr(mfg_dec, "source_image", None)

        has_pincode = is_valid_pincode(extracted_val)
        has_adequate_length = len(extracted_val) >= 15

        if not has_pincode:
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.WARNING,
                severity=Severity.HIGH,
                weight=self.weight,
                message="Manufacturer address is declared but missing a valid 6-digit postal PIN code.",
                detected_value=extracted_val,
                expected_value="Complete postal address with 6-digit PIN code",
                legal_reference=self.legal_reference,
                evidence_image=source_img,
            )

        if not has_adequate_length:
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.WARNING,
                severity=Severity.MEDIUM,
                weight=self.weight,
                message="Manufacturer address appears abbreviated or incomplete.",
                detected_value=extracted_val,
                expected_value="Complete street, city, state and PIN address",
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
            message="Complete manufacturer/packer details and postal PIN code verified.",
            detected_value=norm_val,
            expected_value="Complete manufacturer details",
            legal_reference=self.legal_reference,
            evidence_image=source_img,
        )
