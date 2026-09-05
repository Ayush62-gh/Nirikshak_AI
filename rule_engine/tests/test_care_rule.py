"""
Unit tests for LM-RULE-CARE-008: Consumer Care Details Declaration Check.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_care_rule_pass():
    payload = {
        "productId": "TEST-CARE-01",
        "consumerCare": "Email: care@maker.com, Tel: 1800-111-2222",
        "isImported": False,
        "productName": "Item",
        "manufacturerName": "Maker",
        "manufacturerAddress": "Address",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    care_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-CARE-008")
    assert care_res["status"] == "PASS"


def test_care_rule_missing_fail():
    payload = {
        "productId": "TEST-CARE-02",
        "consumerCare": None,
        "isImported": False,
        "productName": "Item",
        "manufacturerName": "Maker",
        "manufacturerAddress": "Address",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    care_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-CARE-008")
    assert care_res["status"] == "FAIL"


def test_care_rule_unverified_manual_review():
    payload = {
        "productId": "TEST-CARE-03",
        "consumerCare": "Contact Officer",  # Text present but missing phone or email format
        "isImported": False,
        "productName": "Item",
        "manufacturerName": "Maker",
        "manufacturerAddress": "Address",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    care_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-CARE-008")
    assert care_res["status"] == "MANUAL_REVIEW"
