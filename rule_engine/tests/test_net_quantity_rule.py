"""
Unit tests for LM-RULE-NETQTY-002: Net Quantity Declaration Check.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_net_quantity_categories_pass():
    categories_to_test = [
        ("WEIGHT", "250 g"),
        ("VOLUME", "500 ml"),
        ("LENGTH", "10 m"),
        ("AREA", "5 sq m"),
        ("NUMBER_OR_UNIT", "10 pcs")
    ]
    for cat_name, qty_val in categories_to_test:
        payload = {
            "productId": f"TEST-QTY-{cat_name}",
            "netQuantity": qty_val,
            "mrp": "Rs. 100 (incl. of all taxes)",
            "isImported": False,
            "productName": "Item",
            "manufacturerName": "Maker",
            "manufacturerAddress": "Address",
            "monthOfPacking": "08",
            "yearOfPacking": "2026",
            "consumerCare": "care@maker.com"
        }
        res = client.post("/api/rules/evaluate", json=payload)
        assert res.status_code == 200
        qty_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-NETQTY-002")
        assert qty_res["status"] == "PASS"
        assert cat_name.lower() in qty_res["message"].lower()



def test_net_quantity_unsupported_unit_manual_review():
    payload = {
        "productId": "TEST-QTY-UNSUPPORTED",
        "netQuantity": "16 fluid oz",
        "mrp": "Rs. 100 (incl. of all taxes)",
        "isImported": False,
        "productName": "Item",
        "manufacturerName": "Maker",
        "manufacturerAddress": "Address",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@maker.com"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    qty_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-NETQTY-002")
    assert qty_res["status"] == "MANUAL_REVIEW"


def test_net_quantity_missing_fail():
    payload = {
        "productId": "TEST-QTY-MISSING",
        "netQuantity": None,
        "mrp": "Rs. 100 (incl. of all taxes)",
        "isImported": False,
        "productName": "Item",
        "manufacturerName": "Maker",
        "manufacturerAddress": "Address",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@maker.com"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    qty_res = next(r for r in res.json()["individualRuleResults"] if r["ruleId"] == "LM-RULE-NETQTY-002")
    assert qty_res["status"] == "FAIL"
