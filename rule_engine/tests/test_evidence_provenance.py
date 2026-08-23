"""
Unit & Integration tests for Evidence & Provenance Layer.
Verifies AI/OCR evidence separation, confidence metadata, and decision trace.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_default_structured_input_evidence_provenance():
    """Test 1: Standard input payloads default to STRUCTURED_INPUT evidence source with 1.0 confidence."""
    payload = {
        "productId": "TEST-EV-01",
        "productName": "Green Tea",
        "isImported": False,
        "manufacturerName": "Tea Co",
        "manufacturerAddress": "Noida",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@teaco.com"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["decisionTrace"]["summary"]["pass"] > 0
    assert "STRUCTURED_INPUT" in data["decisionTrace"]["evidenceSources"]

    mrp_rule = next(r for r in data["individualRuleResults"] if r["ruleId"] == "LM-RULE-MRP-001")
    assert mrp_rule["evidence"]["source"] == "STRUCTURED_INPUT"
    assert mrp_rule["evidence"]["confidence"] == 1.0
    assert mrp_rule["evidence"]["field"] == "mrp"


def test_ocr_ready_evidence_ingestion():
    """Test 2: System ingests custom OCR evidence source and confidence metadata."""
    payload = {
        "productId": "TEST-EV-02",
        "productName": "Imported Tea",
        "isImported": True,
        "importerName": "Global Imports Ltd",
        "netQuantity": "200 g",
        "mrp": "Rs. 450 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@global.com",
        "fieldEvidence": {
            "importerName": {
                "field": "importerName",
                "value": "Global Imports Ltd",
                "source": "OCR",
                "confidence": 0.96,
                "rawAnnotation": "BoundingBox[100,200,300,220]"
            }
        }
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()

    imp_rule = next(r for r in data["individualRuleResults"] if r["ruleId"] == "LM-RULE-IMP-003")
    assert imp_rule["evidence"]["source"] == "OCR"
    assert imp_rule["evidence"]["confidence"] == 0.96
    assert imp_rule["evidence"]["rawAnnotation"] == "BoundingBox[100,200,300,220]"
    assert "OCR" in data["decisionTrace"]["evidenceSources"]


def test_ai_ocr_separation_from_compliance_decision():
    """
    Test 3: CRITICAL REGRESSION TEST.
    AI/OCR detects '₹199' with high confidence (0.99), BUT statutory tax clause is missing.
    Verify that rule engine returns MANUAL_REVIEW, proving AI confidence does NOT force a PASS.
    """
    payload = {
        "productId": "TEST-EV-03",
        "productName": "Earl Grey Tea",
        "isImported": False,
        "manufacturerName": "Tea Co",
        "manufacturerAddress": "Noida",
        "netQuantity": "100 g",
        "mrp": "₹199",  # Numeric price detected, but 'incl. of all taxes' is missing
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@teaco.com",
        "fieldEvidence": {
            "mrp": {
                "field": "mrp",
                "value": "₹199",
                "source": "OCR",
                "confidence": 0.99,  # High AI confidence
                "rawAnnotation": "OCR Text '₹199'"
            }
        }
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()

    mrp_rule = next(r for r in data["individualRuleResults"] if r["ruleId"] == "LM-RULE-MRP-001")
    assert mrp_rule["status"] == "MANUAL_REVIEW"
    assert mrp_rule["evidence"]["source"] == "OCR"
    assert mrp_rule["evidence"]["confidence"] == 0.99
    # Proves deterministic rule logic override: High confidence AI extraction does NOT force a statutory PASS
    assert data["overallStatus"] == "MANUAL_REVIEW"


def test_missing_evidence_graceful_handling():
    """Test 4: Missing or None field values handle evidence creation without crashing."""
    payload = {
        "productId": "TEST-EV-04",
        "productName": "Tea",
        "isImported": False,
        "manufacturerName": None,
        "manufacturerAddress": None,
        "netQuantity": "100 g",
        "mrp": None
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()

    mrp_rule = next(r for r in data["individualRuleResults"] if r["ruleId"] == "LM-RULE-MRP-001")
    assert mrp_rule["status"] == "FAIL"
    assert mrp_rule["evidence"]["field"] == "mrp"
    assert mrp_rule["evidence"]["value"] is None
    assert mrp_rule["evidence"]["source"] == "STRUCTURED_INPUT"


def test_backward_compatibility_payloads():
    """Test 5: Payloads from previous phases without fieldEvidence continue to work identically."""
    payload = {
        "productId": "TEST-EV-05",
        "productName": "Organic Herbal Tea",
        "isImported": False,
        "manufacturerName": "Ayurveda Organics Ltd",
        "manufacturerAddress": "Haridwar, Uttarakhand - 249401",
        "netQuantity": "100 g",
        "mrp": "Rs. 299.00 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@ayurveda.com"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["overallStatus"] == "PASS"
    assert data["failedRules"] == 0
    assert data["manualReviewRules"] == 0
    assert len(data["individualRuleResults"]) >= 8
