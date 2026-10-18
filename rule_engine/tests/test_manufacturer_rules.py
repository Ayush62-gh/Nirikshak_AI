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
        "manufacturerAddress": "Darjeeling Factory - 734101",
        "productName": "Item",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@maker.com",
        "unitSalePrice": "Rs 2.00/g"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    addr_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-MFGADDR-006")
    assert addr_res["status"] == "PASS"


def test_manufacturer_address_missing_pincode_manual_review():
    payload = {
        "productId": "TEST-MFG-03B",
        "isImported": False,
        "manufacturerName": "Maker",
        "manufacturerAddress": "Darjeeling Factory",  # Missing 6-digit pincode -> MANUAL_REVIEW
        "productName": "Item",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@maker.com",
        "unitSalePrice": "Rs 2.00/g"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    addr_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-MFGADDR-006")
    assert addr_res["status"] == "MANUAL_REVIEW"


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


def test_manufacturer_address_spaced_pincode_pass():
    payload = {
        "productId": "TEST-MFG-05",
        "isImported": False,
        "manufacturerName": "Maker",
        "manufacturerAddress": "Mumbai - 400 001",
        "productName": "Item",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    addr_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-MFGADDR-006")
    assert addr_res["status"] == "PASS"


def test_manufacturer_address_pin_prefix_pass():
    payload = {
        "productId": "TEST-MFG-06",
        "isImported": False,
        "manufacturerName": "Maker",
        "manufacturerAddress": "Pin: 560001",
        "productName": "Item",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    addr_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-MFGADDR-006")
    assert addr_res["status"] == "PASS"


def test_manufacturer_address_no_pincode_manual_review():
    payload = {
        "productId": "TEST-MFG-07",
        "isImported": False,
        "manufacturerName": "Maker",
        "manufacturerAddress": "Bangalore, Karnataka",
        "productName": "Item",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    addr_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-MFGADDR-006")
    assert addr_res["status"] == "MANUAL_REVIEW"


def test_manufacturer_address_fssai_no_pincode_manual_review():
    payload = {
        "productId": "TEST-MFG-08",
        "isImported": False,
        "manufacturerName": "Maker",
        "manufacturerAddress": "FSSAI 10020021000123",
        "productName": "Item",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    addr_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-MFGADDR-006")
    assert addr_res["status"] == "MANUAL_REVIEW"


def test_manufacturer_address_batch_number_limitation_pass():
    # Known limitation: 6-digit numbers like batch numbers ("123456") in address text are matched by regex as pincodes and evaluate to PASS.
    payload = {
        "productId": "TEST-MFG-09",
        "isImported": False,
        "manufacturerName": "Maker",
        "manufacturerAddress": "Batch No 123456, Delhi",
        "productName": "Item",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    addr_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-MFGADDR-006")
    assert addr_res["status"] == "PASS"

