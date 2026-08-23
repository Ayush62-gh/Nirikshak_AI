"""
Unit tests for Manufacturer Name (LM-RULE-MFGNAME-005) and Address (LM-RULE-MFGADDR-006) Rules.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_manufacturer_name_pass():
    payload = {
        "productId": "TEST-MFG-01",
        "isImported": False,
        "manufacturerName": "AB",  # Short name without arbitrary string length penalty
        "manufacturerAddress": "Address",
        "productName": "Item",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@maker.com"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    mfg_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-MFGNAME-005")
    assert mfg_res["status"] == "PASS"


def test_manufacturer_name_missing_fail():
    payload = {
        "productId": "TEST-MFG-02",
        "isImported": False,
        "manufacturerName": None,
        "packerName": None,
        "manufacturerAddress": "Address",
        "productName": "Item",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@maker.com"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    mfg_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-MFGNAME-005")
    assert mfg_res["status"] == "FAIL"


def test_manufacturer_address_pass():
    payload = {
        "productId": "TEST-MFG-03",
        "isImported": False,
        "manufacturerName": "Maker",
        "manufacturerAddress": "Darjeeling Factory",  # Address present without requiring pincode heuristics
        "productName": "Item",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@maker.com"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    addr_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-MFGADDR-006")
    assert addr_res["status"] == "PASS"


def test_manufacturer_address_missing_fail():
    payload = {
        "productId": "TEST-MFG-04",
        "isImported": False,
        "manufacturerName": "Maker",
        "manufacturerAddress": None,
        "productName": "Item",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@maker.com"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    addr_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-MFGADDR-006")
    assert addr_res["status"] == "FAIL"
