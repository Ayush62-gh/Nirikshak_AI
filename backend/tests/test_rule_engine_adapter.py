import pytest
from app.services.rule_client import (
    _build_rule_engine_request,
    _parse_rule_engine_response,
    validate_compliance,
)


def test_build_rule_engine_request_mapping():
    extracted = {
        "product_id": "test-prod-100",
        "product_name": "Sample Biscuits 200g",
        "manufacturer": "ABC Foods Pvt Ltd",
        "manufacturer_address": "123 Industrial Estate, Delhi",
        "net_quantity": "200 g",
        "mrp": "Rs. 45",
        "mfg_date": "01/2026",
        "consumer_care": "1800-XXX-XXXX",
        "country_of_origin": "India",
        "importer_name": "ABC Importers Pvt Ltd",
        "unit_sale_price": "Rs. 0.225/g",
        "expiry_date": "01/2027",
    }

    request_body = _build_rule_engine_request(extracted)

    assert request_body["productId"] == "test-prod-100"
    assert request_body["productName"] == "Sample Biscuits 200g"
    assert request_body["productType"] is None
    assert request_body["isImported"] is False
    assert request_body["manufacturerName"] == "ABC Foods Pvt Ltd"
    assert request_body["manufacturerAddress"] == "123 Industrial Estate, Delhi"
    assert request_body["packerName"] is None
    assert request_body["importerName"] == "ABC Importers Pvt Ltd"
    assert request_body["netQuantity"] == "200 g"
    assert request_body["mrp"] == "Rs. 45"
    assert request_body["unitSalePrice"] == "Rs. 0.225/g"
    assert request_body["monthOfPacking"] == "01"
    assert request_body["yearOfPacking"] == "2026"
    assert request_body["expiryDate"] == "01/2027"
    assert request_body["consumerCare"] == "1800-XXX-XXXX"
    assert request_body["countryOfOrigin"] == "India"
    assert "fontSizeMm" not in request_body


def test_build_rule_engine_request_product_type_none_and_expiry_handling():
    # Payload built from an extracted dict with no expiry_date has productType None and expiryDate None
    extracted_without_expiry = {
        "product_name": "Generic Product",
    }
    req_no_expiry = _build_rule_engine_request(extracted_without_expiry)
    assert req_no_expiry["productType"] is None
    assert req_no_expiry["expiryDate"] is None

    # Payload with expiry_date "08/2027" has productType None and expiryDate "08/2027"
    extracted_with_expiry = {
        "product_name": "Generic Product",
        "expiry_date": "08/2027",
    }
    req_with_expiry = _build_rule_engine_request(extracted_with_expiry)
    assert req_with_expiry["productType"] is None
    assert req_with_expiry["expiryDate"] == "08/2027"


def test_build_rule_engine_request_no_hardcoded_india():
    # (c) the rule payload no longer contains the hardcoded "India"
    extracted_imported = {
        "product_name": "Belgian Chocolate",
        "country_of_origin": "Belgium",
        "importer_name": "Euro Sweets Ltd",
        "unit_sale_price": "Rs. 2.50/g",
        "expiry_date": "10/2028",
    }
    request_body = _build_rule_engine_request(extracted_imported)
    assert request_body["countryOfOrigin"] == "Belgium"
    assert request_body["countryOfOrigin"] != "India"
    assert request_body["importerName"] == "Euro Sweets Ltd"
    assert request_body["unitSalePrice"] == "Rs. 2.50/g"
    assert request_body["expiryDate"] == "10/2028"
    assert "fontSizeMm" not in request_body

    # When country_of_origin is omitted/None, it must be None, NOT "India"
    extracted_empty = {
        "product_name": "Domestic Flour",
    }
    request_body_empty = _build_rule_engine_request(extracted_empty)
    assert request_body_empty["countryOfOrigin"] is None
    assert request_body_empty["importerName"] is None
    assert request_body_empty["unitSalePrice"] is None
    assert request_body_empty["expiryDate"] is None
    assert "fontSizeMm" not in request_body_empty


def test_build_rule_engine_request_invalid_mfg_date():
    extracted = {
        "mfg_date": "invalid_date_string",
    }

    request_body = _build_rule_engine_request(extracted)

    assert request_body["monthOfPacking"] is None
    assert request_body["yearOfPacking"] is None


def test_parse_rule_engine_response_pass_case():
    rule_engine_res = {
        "productId": "test-prod-100",
        "overallStatus": "PASS",
        "totalRules": 10,
        "passedRules": 10,
        "failedRules": 0,
        "manualReviewRules": 0,
        "notApplicableRules": 0,
        "violations": [],
    }

    parsed = _parse_rule_engine_response(rule_engine_res)

    assert parsed["status"] == "COMPLIANT"
    assert parsed["violations"] == []


def test_parse_rule_engine_response_fail_case_with_remediation():
    rule_engine_res = {
        "productId": "test-prod-100",
        "overallStatus": "FAIL",
        "totalRules": 10,
        "passedRules": 8,
        "failedRules": 2,
        "violations": [
            {
                "ruleId": "R001",
                "ruleName": "Rule 6 - Net Quantity",
                "severity": "HIGH",
                "message": "Net quantity symbol format invalid.",
                "field": "netQuantity",
                "remediation": "Use standard unit 'g' or 'kg' instead of 'gms'",
            }
        ],
    }

    parsed = _parse_rule_engine_response(rule_engine_res)

    assert parsed["status"] == "NON_COMPLIANT"
    assert len(parsed["violations"]) == 1
    v = parsed["violations"][0]
    assert v["rule"] == "Rule 6 - Net Quantity"
    assert v["field"] == "netQuantity"
    assert "Net quantity symbol format invalid" in v["description"]
    assert "Suggested fix: Use standard unit 'g' or 'kg' instead of 'gms'" in v["description"]
    assert ".." not in v["description"]
    assert v["description"] == "Net quantity symbol format invalid. Suggested fix: Use standard unit 'g' or 'kg' instead of 'gms'"


def test_parse_rule_engine_response_manual_review_case():
    rule_engine_res = {
        "productId": "test-prod-100",
        "overallStatus": "MANUAL_REVIEW",
        "violations": [],
    }

    parsed = _parse_rule_engine_response(rule_engine_res)

    assert parsed["status"] == "PARTIAL"


def test_build_rule_engine_request_forwards_font_size_mm():
    """Verify font_size_mm is forwarded to Rule Engine as fontSizeMm when present, omitted when None."""
    extracted = {
        "product_name": "Test Biscuits",
        "font_size_mm": 3.0,
    }
    req = _build_rule_engine_request(extracted)
    assert req["fontSizeMm"] == 3.0

    extracted_none = {
        "product_name": "Test Biscuits",
        "font_size_mm": None,
    }
    req_none = _build_rule_engine_request(extracted_none)
    assert "fontSizeMm" not in req_none
