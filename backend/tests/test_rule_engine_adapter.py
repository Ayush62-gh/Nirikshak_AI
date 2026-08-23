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
        "net_quantity": "200 g",
        "mrp": "Rs. 45",
        "mfg_date": "01/2026",
        "consumer_care": "1800-XXX-XXXX",
    }

    request_body = _build_rule_engine_request(extracted)

    assert request_body["productId"] == "test-prod-100"
    assert request_body["productName"] == "Sample Biscuits 200g"
    assert request_body["productType"] == "food"
    assert request_body["isImported"] is False
    assert request_body["manufacturerName"] == "ABC Foods Pvt Ltd"
    assert request_body["manufacturerAddress"] is None
    assert request_body["netQuantity"] == "200 g"
    assert request_body["mrp"] == "Rs. 45"
    assert request_body["monthOfPacking"] == "01"
    assert request_body["yearOfPacking"] == "2026"
    assert request_body["consumerCare"] == "1800-XXX-XXXX"
    assert request_body["countryOfOrigin"] == "India"


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
