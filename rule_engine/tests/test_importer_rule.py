"""
Unit tests for LM-RULE-IMP-003: Importer Name & Address Check.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_importer_imported_pass():
    payload = {
        "productId": "TEST-IMP-01",
        "isImported": True,
        "importerName": "Global Imports Pvt Ltd",
        "productName": "Imported Item",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@global.com"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    imp_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-IMP-003")
    assert imp_res["status"] == "PASS"


def test_importer_imported_missing_fail():
    payload = {
        "productId": "TEST-IMP-02",
        "isImported": True,
        "importerName": None,
        "productName": "Imported Item",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@global.com"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    imp_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-IMP-003")
    assert imp_res["status"] == "FAIL"


def test_importer_unconfirmed_manual_review():
    payload = {
        "productId": "TEST-IMP-03",
        "isImported": None,  # Unconfirmed import status
        "productName": "Item",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@global.com"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    imp_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-IMP-003")
    assert imp_res["status"] == "MANUAL_REVIEW"


def test_importer_domestic_not_applicable():
    payload = {
        "productId": "TEST-IMP-04",
        "isImported": False,  # Explicitly domestic
        "productName": "Domestic Item",
        "manufacturerName": "Maker",
        "manufacturerAddress": "Address",
        "netQuantity": "100 g",
        "mrp": "Rs. 200 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@maker.com"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    imp_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-IMP-003")
    assert imp_res["status"] == "NOT_APPLICABLE"
