from typing import Any, Dict, Optional
from compliance_engine.rules.base_rule import BaseRule, RuleResult, RuleStatus
from compliance_engine.severity import Severity
from app.utils.validators import is_valid_email, is_valid_phone


class ConsumerCareEmailRule(BaseRule):
    """
    Legal Metrology Rule 6(1)(g):
    Every package must declare the consumer care email address for consumer complaints.
    """

    def evaluate(
        self, declarations: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        email_dec = declarations.get("consumer_care_email")

        if not email_dec:
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.FAIL,
                severity=self.severity,
                weight=self.weight,
                message="Mandatory Consumer Care email address is missing on the package.",
                detected_value=None,
                expected_value="Valid consumer care email (e.g. feedback@company.com)",
                legal_reference=self.legal_reference,
            )

        extracted_val = getattr(email_dec, "extracted_value", str(email_dec))
        norm_val = getattr(email_dec, "normalized_value", extracted_val)
        source_img = getattr(email_dec, "source_image", None)

        if not is_valid_email(norm_val):
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.WARNING,
                severity=Severity.HIGH,
                weight=self.weight,
                message=f"Consumer care email format '{norm_val}' is invalid.",
                detected_value=extracted_val,
                expected_value="Valid standard email address",
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
            message="Valid consumer care email address declared.",
            detected_value=norm_val,
            expected_value="Valid email address",
            legal_reference=self.legal_reference,
            evidence_image=source_img,
        )


class ConsumerCarePhoneRule(BaseRule):
    """
    Legal Metrology Rule 6(1)(g):
    Every package must declare a telephone/toll-free helpline number for consumer complaints.
    """

    def evaluate(
        self, declarations: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        phone_dec = declarations.get("consumer_care_phone")

        if not phone_dec:
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.FAIL,
                severity=self.severity,
                weight=self.weight,
                message="Mandatory Consumer Care helpline/telephone number is missing on the package.",
                detected_value=None,
                expected_value="Toll-free / Customer helpline telephone number",
                legal_reference=self.legal_reference,
            )

        extracted_val = getattr(phone_dec, "extracted_value", str(phone_dec))
        norm_val = getattr(phone_dec, "normalized_value", extracted_val)
        source_img = getattr(phone_dec, "source_image", None)

        if not is_valid_phone(extracted_val):
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.WARNING,
                severity=Severity.MEDIUM,
                weight=self.weight,
                message=f"Helpline number '{extracted_val}' may not be a complete phone number.",
                detected_value=extracted_val,
                expected_value="Valid 10-digit or 1800-toll-free helpline number",
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
            message="Valid consumer care phone / helpline declared.",
            detected_value=norm_val,
            expected_value="Valid phone number",
            legal_reference=self.legal_reference,
            evidence_image=source_img,
        )
