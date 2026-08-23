"""
Unit tests for LM-RULE-MRP-001: Maximum Retail Price Declaration Check.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_mrp_rule_pass():
    payload = {
        "productId": "TEST-MRP-01",
        "mrp": "Rs. 250.00 (incl. of all taxes)",
        "isImported": False,
        "productName": "Tea",
        "manufacturerName": "Tea Co",
        "manufacturerAddress": "Noida",
        "netQuantity": "100 g",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@teaco.com"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    mrp_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-MRP-001")
    assert mrp_res["status"] == "PASS"
    assert mrp_res["field"] == "mrp"


def test_mrp_rule_missing_fail():
    payload = {
        "productId": "TEST-MRP-02",
        "mrp": None,
        "isImported": False,
        "productName": "Tea",
        "manufacturerName": "Tea Co",
        "manufacturerAddress": "Noida",
        "netQuantity": "100 g",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@teaco.com"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    mrp_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-MRP-001")
    assert mrp_res["status"] == "FAIL"


def test_mrp_rule_unverified_presentation_manual_review():
    payload = {
        "productId": "TEST-MRP-03",
        "mrp": "350",  # Numeric price present, but statutory presentation / tax phrase unverified
        "isImported": False,
        "productName": "Tea",
        "manufacturerName": "Tea Co",
        "manufacturerAddress": "Noida",
        "netQuantity": "100 g",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@teaco.com"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    mrp_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-MRP-001")
    assert mrp_res["status"] == "MANUAL_REVIEW"
