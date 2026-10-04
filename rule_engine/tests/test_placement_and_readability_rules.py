"""
Unit tests for Declaration Placement (LM-RULE-PLACE-013) and Physical Legibility/Contrast (LM-RULE-READ-014) Rules.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_declaration_placement_pdp_valid_pass():
    payload = {
        "productId": "TEST-PLACE-01",
        "productName": "Tea",
        "isImported": False,
        "manufacturerName": "Maker",
        "manufacturerAddress": "Delhi - 110001",
        "netQuantity": "100 g",
        "mrp": "Rs. 100 (incl. of all taxes)",
        "declarationPlacement": "Front Panel - Principal Display Panel",
        "isPDPPlacementValid": True
    }
    res = client.post("/api/v1/compliance/check", json=payload)
    assert res.status_code == 200
    rule = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-PLACE-013")
    assert rule["status"] == "PASS"


def test_declaration_placement_invalid_fail():
    payload = {
        "productId": "TEST-PLACE-02",
        "productName": "Tea",
        "isImported": False,
        "isPDPPlacementValid": False
    }
    res = client.post("/api/v1/compliance/check", json=payload)
    assert res.status_code == 200
    rule = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-PLACE-013")
    assert rule["status"] == "FAIL"


def test_readability_contrast_high_pass():
    payload = {
        "productId": "TEST-READ-01",
        "productName": "Tea",
        "isImported": False,
        "contrastRatio": 7.5,
        "isLegible": True
    }
    res = client.post("/api/v1/compliance/check", json=payload)
    assert res.status_code == 200
    rule = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-READ-014")
    assert rule["status"] == "PASS"


def test_readability_contrast_low_fail():
    payload = {
        "productId": "TEST-READ-02",
        "productName": "Tea",
        "isImported": False,
        "contrastRatio": 2.1,
        "isLegible": False
    }
    res = client.post("/api/v1/compliance/check", json=payload)
    assert res.status_code == 200
    rule = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-READ-014")
    assert rule["status"] == "FAIL"
