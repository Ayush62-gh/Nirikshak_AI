from typing import Any, Dict, Optional
from compliance_engine.rules.base_rule import BaseRule, RuleResult, RuleStatus
from compliance_engine.severity import Severity


class ReadabilityRule(BaseRule):
    """
    Legal Metrology Rule 9(1):
    Declarations shall be legible, prominent, and clearly visible with adequate contrast against the background.
    """

    def evaluate(
        self, declarations: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        mean_confidence = context.get("ocr_mean_confidence", 0.90) if context else 0.90

        if mean_confidence < 0.60:
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.WARNING,
                severity=Severity.MEDIUM,
                weight=self.weight,
                message=f"Average label readability score ({int(mean_confidence * 100)}%) is below acceptable clarity threshold (60%).",
                detected_value=f"{int(mean_confidence * 100)}% clarity",
                expected_value="Minimum 60% OCR legibility clarity",
                legal_reference=self.legal_reference,
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_number=self.rule_number,
            name=self.name,
            category=self.category,
            status=RuleStatus.PASS,
            severity=self.severity,
            weight=self.weight,
            message="Package declarations exhibit adequate visual legibility and contrast.",
            detected_value=f"{int(mean_confidence * 100)}% clarity",
            expected_value="Legible declarations",
            legal_reference=self.legal_reference,
        )


class PhysicalFontSizeRule(BaseRule):
    """
    Legal Metrology (Packaged Commodities) Rule 9(2) & Table:
    Minimum height of letters and numerals based on package principal display panel (PDP) area.
    
    Architectural Principle:
    Physical font size (in mm) cannot be accurately deduced solely by pixel dimensions in OCR.
    This rule consumes calibrated physical measurements provided by an optical/calibrated
    computer vision measurement service when physical package dimensions or DPI calibrations are provided.
    """

    def evaluate(
        self, declarations: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        # Check if calibrated physical measurement data is available in context
        cv_measurement = context.get("cv_font_measurement") if context else None

        if not cv_measurement:
            # Physical measurement data not yet provided / pending calibration
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.NOT_APPLICABLE,
                severity=Severity.INFO,
                weight=self.weight,
                message=(
                    "Physical font-size millimeter measurement requires calibrated optical "
                    "or computer-vision dimensional input."
                ),
                detected_value="Awaiting physical scale calibration",
                expected_value="Minimum font height in mm per Rule 9(2) schedule",
                legal_reference=self.legal_reference,
            )

        measured_height_mm = cv_measurement.get("numeral_height_mm", 0.0)
        required_min_height_mm = cv_measurement.get("required_min_height_mm", 1.5)

        if measured_height_mm < required_min_height_mm:
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.FAIL,
                severity=Severity.HIGH,
                weight=self.weight,
                message=(
                    f"Measured numeral font height ({measured_height_mm}mm) is less than "
                    f"statutory minimum required ({required_min_height_mm}mm) for this PDP area."
                ),
                detected_value=f"{measured_height_mm} mm",
                expected_value=f">= {required_min_height_mm} mm",
                legal_reference=self.legal_reference,
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_number=self.rule_number,
            name=self.name,
            category=self.category,
            status=RuleStatus.PASS,
            severity=self.severity,
            weight=self.weight,
            message="Numeral and letter height complies with statutory minimum height requirements.",
            detected_value=f"{measured_height_mm} mm",
            expected_value=f">= {required_min_height_mm} mm",
            legal_reference=self.legal_reference,
        )
