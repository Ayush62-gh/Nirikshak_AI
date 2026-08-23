import io
from PIL import Image
import pytest
from httpx import AsyncClient

from compliance_engine.compliance_score import ComplianceScoreCalculator
from compliance_engine.rule_engine import LegalMetrologyComplianceEngine
from compliance_engine.rule_registry import RuleRegistry
from compliance_engine.rules.base_rule import RuleResult, RuleStatus
from compliance_engine.rules.consumer_care_rules import (
    ConsumerCareEmailRule,
    ConsumerCarePhoneRule,
)
from compliance_engine.rules.date_rules import DateDeclarationRule
from compliance_engine.rules.manufacturer_rules import ManufacturerRule
from compliance_engine.rules.mrp_rules import MRPRule
from compliance_engine.rules.quantity_rules import NetQuantityRule
from compliance_engine.severity import Severity
from app.models.inspection import ComplianceResultStatus
from app.services.extraction_service import ExtractedDeclaration


def test_rule_registry_loads_json():
    """Verify that rules are correctly loaded and mapped to their handler classes from JSON."""
    rules = RuleRegistry.load_rules_from_json()
    assert len(rules) >= 7

    rule_ids = [r.rule_id for r in rules]
    assert "LM-PC-001" in rule_ids  # MRP
    assert "LM-PC-002" in rule_ids  # Net Qty
    assert "LM-PC-003" in rule_ids  # Mfg Date
    assert "LM-PC-004" in rule_ids  # Manufacturer
    assert "LM-PC-005" in rule_ids  # Consumer email


def test_mrp_rule_evaluation():
    """Test MRP rule validation states."""
    rule = MRPRule({
        "rule_id": "LM-PC-001",
        "name": "Mandatory MRP",
        "category": "MRP",
        "severity": "CRITICAL",
        "weight": 20,
    })

    # 1. Missing MRP -> FAIL
    res_missing = rule.evaluate({})
    assert res_missing.status == RuleStatus.FAIL
    assert res_missing.severity == Severity.CRITICAL

    # 2. MRP without tax inclusive statement -> FAIL (Rule 6(1)(e))
    decl_no_tax = {
        "mrp": ExtractedDeclaration(
            declaration_type="mrp",
            extracted_value="MRP Rs. 100.00",
            normalized_value="Rs. 100.00",
            confidence=0.9,
            is_valid=False,
        )
    }
    res_no_tax = rule.evaluate(decl_no_tax)
    assert res_no_tax.status == RuleStatus.FAIL

    # 3. Valid MRP with inclusive of taxes -> PASS
    decl_valid = {
        "mrp": ExtractedDeclaration(
            declaration_type="mrp",
            extracted_value="MRP Rs. 100.00 (incl. of all taxes)",
            normalized_value="Rs. 100.00 (incl. of all taxes)",
            confidence=0.95,
            is_valid=True,
        )
    }
    res_valid = rule.evaluate(decl_valid)
    assert res_valid.status == RuleStatus.PASS


def test_net_quantity_rule():
    """Test Net Quantity rule validation and standard unit checking."""
    rule = NetQuantityRule({
        "rule_id": "LM-PC-002",
        "name": "Net Quantity",
        "category": "QUANTITY",
        "severity": "CRITICAL",
        "weight": 20,
    })

    # Valid SI unit
    res_pass = rule.evaluate({
        "net_quantity": ExtractedDeclaration(
            declaration_type="net_quantity",
            extracted_value="Net Qty: 500 g",
            normalized_value="500 g",
            confidence=0.95,
        )
    })
    assert res_pass.status == RuleStatus.PASS

    # Non-standard unit -> WARNING
    res_warn = rule.evaluate({
        "net_quantity": ExtractedDeclaration(
            declaration_type="net_quantity",
            extracted_value="Net Qty: 500 packets",
            normalized_value="500 packets",
            confidence=0.90,
        )
    })
    assert res_warn.status == RuleStatus.WARNING


def test_manufacturer_rule_pincode():
    """Test Manufacturer rule requires PIN code for complete postal address."""
    rule = ManufacturerRule({
        "rule_id": "LM-PC-004",
        "name": "Manufacturer",
        "category": "MANUFACTURER",
        "severity": "HIGH",
        "weight": 15,
    })

    # Without PIN code -> WARNING
    res_no_pin = rule.evaluate({
        "manufacturer": ExtractedDeclaration(
            declaration_type="manufacturer",
            extracted_value="Manufactured by: Tasty Foods, Sector 4, Gurgaon, Haryana",
            normalized_value="Tasty Foods, Sector 4, Gurgaon, Haryana",
            confidence=0.85,
        )
    })
    assert res_no_pin.status == RuleStatus.WARNING

    # With valid 6-digit PIN code -> PASS
    res_pin = rule.evaluate({
        "manufacturer": ExtractedDeclaration(
            declaration_type="manufacturer",
            extracted_value="Manufactured by: Tasty Foods, Sector 4, Gurgaon, Haryana - 122001",
            normalized_value="Tasty Foods, Sector 4, Gurgaon, Haryana - 122001",
            confidence=0.95,
        )
    })
    assert res_pin.status == RuleStatus.PASS


def test_compliance_scoring_system():
    """Verify weighted compliance score calculation and critical failure handling."""
    # Scenario 1: All rules pass
    results_pass = [
        RuleResult(rule_id="1", name="R1", category="MRP", status=RuleStatus.PASS, severity=Severity.CRITICAL, weight=20, message=""),
        RuleResult(rule_id="2", name="R2", category="QUANTITY", status=RuleStatus.PASS, severity=Severity.CRITICAL, weight=20, message=""),
        RuleResult(rule_id="3", name="R3", category="DATE", status=RuleStatus.PASS, severity=Severity.HIGH, weight=15, message=""),
    ]
    score_pass = ComplianceScoreCalculator.calculate(results_pass)
    assert score_pass.percentage == 100.0
    assert score_pass.status == ComplianceResultStatus.COMPLIANT

    # Scenario 2: Critical failure -> overall status is NON_COMPLIANT regardless of score
    results_critical_fail = [
        RuleResult(rule_id="1", name="R1", category="MRP", status=RuleStatus.FAIL, severity=Severity.CRITICAL, weight=20, message=""),
        RuleResult(rule_id="2", name="R2", category="QUANTITY", status=RuleStatus.PASS, severity=Severity.CRITICAL, weight=20, message=""),
        RuleResult(rule_id="3", name="R3", category="DATE", status=RuleStatus.PASS, severity=Severity.HIGH, weight=15, message=""),
        RuleResult(rule_id="4", name="R4", category="MANUFACTURER", status=RuleStatus.PASS, severity=Severity.HIGH, weight=15, message=""),
    ]
    score_crit = ComplianceScoreCalculator.calculate(results_critical_fail)
    assert score_crit.status == ComplianceResultStatus.NON_COMPLIANT
    assert score_crit.critical_failures == 1


@pytest.mark.asyncio
async def test_full_pipeline_api_execution(client: AsyncClient):
    """Test full scan pipeline API execution on an inspection."""
    # 1. Register Inspector
    reg_payload = {
        "name": "Inspector Divya",
        "email": "divya.metrology@gov.in",
        "password": "Password123!",
        "role": "INSPECTOR",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Inspection
    insp_payload = {
        "product_name": "Herbal Green Tea 100g",
        "barcode": "8905556667778",
        "category": "Beverages",
    }
    res_insp = await client.post("/api/v1/inspections", json=insp_payload, headers=headers)
    insp_id = res_insp.json()["data"]["id"]

    # 3. Upload Valid Image
    img = Image.new("RGB", (300, 300), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    files = [("images", ("label.jpg", buf, "image/jpeg"))]
    await client.post(f"/api/v1/inspections/{insp_id}/images", files=files, headers=headers)

    # 4. Trigger Scan Pipeline
    res_scan = await client.post(f"/api/v1/inspections/{insp_id}/scan", headers=headers)
    assert res_scan.status_code == 200
    scan_data = res_scan.json()["data"]

    assert scan_data["status"] == "COMPLETED"
    assert scan_data["compliance_score"] is not None
    assert len(scan_data["declarations"]) > 0
    assert scan_data["overall_result"] in ["COMPLIANT", "NON_COMPLIANT", "WARNING"]
