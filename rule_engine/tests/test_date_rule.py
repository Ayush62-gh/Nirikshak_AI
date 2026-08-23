"""
Unit tests for LM-RULE-DATE-007: Month and Year of Packing Check.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_date_rule_pass():
    payload = {
        "productId": "TEST-DATE-01",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "isImported": False,
        "productName": "Item",
        "manufacturerName": "Maker",
        "manufacturerAddress": "Address",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)",
        "consumerCare": "care@maker.com"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    date_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-DATE-007")
    assert date_res["status"] == "PASS"


def test_date_rule_missing_fail():
    payload = {
        "productId": "TEST-DATE-02",
        "monthOfPacking": None,
        "yearOfPacking": None,
        "isImported": False,
        "productName": "Item",
        "manufacturerName": "Maker",
        "manufacturerAddress": "Address",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)",
        "consumerCare": "care@maker.com"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    date_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-DATE-007")
    assert date_res["status"] == "FAIL"


def test_date_rule_unverified_format_manual_review():
    payload = {
        "productId": "TEST-DATE-03",
        "monthOfPacking": "99",  # Invalid month string
        "yearOfPacking": "2026",
        "isImported": False,
        "productName": "Item",
        "manufacturerName": "Maker",
        "manufacturerAddress": "Address",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)",
        "consumerCare": "care@maker.com"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    date_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-DATE-007")
    assert date_res["status"] == "MANUAL_REVIEW"
