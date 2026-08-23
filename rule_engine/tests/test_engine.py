"""
Integration & Pipeline Tests for Rule Engine Core.
Verifies status precedence, deterministic execution, and pipeline edge cases.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_engine_deterministic_execution():
    """Verifies that executing the same payload multiple times yields identical results."""
    payload = {
        "productId": "PROD-DET-01",
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

    res1 = client.post("/api/rules/evaluate", json=payload).json()
    res2 = client.post("/api/rules/evaluate", json=payload).json()

    assert res1["overallStatus"] == res2["overallStatus"]
    assert res1["passedRules"] == res2["passedRules"]
    assert res1["failedRules"] == res2["failedRules"]
    assert res1["manualReviewRules"] == res2["manualReviewRules"]
    assert res1["individualRuleResults"] == res2["individualRuleResults"]


def test_engine_sequential_evaluation_isolation():
    """Verifies that evaluating product A does not leak state into product B."""
    payload_a = {
        "productId": "PROD-A",
        "productName": "Product A",
        "isImported": True,
        "importerName": "Importer A",
        "netQuantity": "100 g",
        "mrp": "Rs. 100 (incl. of all taxes)",
        "monthOfPacking": "01",
        "yearOfPacking": "2026",
        "consumerCare": "care@a.com"
    }

    payload_b = {
        "productId": "PROD-B",
        "productName": "Product B",
        "isImported": False,
        "manufacturerName": "Maker B",
        "manufacturerAddress": "Address B",
        "netQuantity": "200 g",
        "mrp": "Rs. 200 (incl. of all taxes)",
        "monthOfPacking": "02",
        "yearOfPacking": "2026",
        "consumerCare": "care@b.com"
    }

    res_a = client.post("/api/rules/evaluate", json=payload_a).json()
    res_b = client.post("/api/rules/evaluate", json=payload_b).json()

    assert res_a["productId"] == "PROD-A"
    assert res_b["productId"] == "PROD-B"
    # Importer rule applies to A, NOT_APPLICABLE for B
    imp_a = next(r for r in res_a["individualRuleResults"] if r["ruleId"] == "LM-RULE-IMP-003")
    imp_b = next(r for r in res_b["individualRuleResults"] if r["ruleId"] == "LM-RULE-IMP-003")
    assert imp_a["status"] == "PASS"
    assert imp_b["status"] == "NOT_APPLICABLE"


def test_engine_status_precedence_all_cases():
    """
    Verifies Status Precedence Order:
    FAIL > MANUAL_REVIEW > PASS > NOT_APPLICABLE
    """
    # 1. PASS + PASS -> PASS
    payload_pass = {
        "productId": "PREC-1",
        "productName": "Tea",
        "isImported": False,
        "manufacturerName": "Maker",
        "manufacturerAddress": "Addr",
        "netQuantity": "100 g",
        "mrp": "Rs. 100 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@maker.com"
    }
    r_pass = client.post("/api/rules/evaluate", json=payload_pass).json()
    assert r_pass["overallStatus"] == "PASS"

    # 2. PASS + MANUAL_REVIEW -> MANUAL_REVIEW
    payload_review = dict(payload_pass, productId="PREC-2", mrp="100")
    r_review = client.post("/api/rules/evaluate", json=payload_review).json()
    assert r_review["overallStatus"] == "MANUAL_REVIEW"

    # 3. MANUAL_REVIEW + FAIL -> FAIL
    payload_fail = dict(payload_review, productId="PREC-3", netQuantity=None)
    r_fail = client.post("/api/rules/evaluate", json=payload_fail).json()
    assert r_fail["overallStatus"] == "FAIL"


def test_engine_malformed_input_boundary_handling():
    """Verifies that unexpected or boundary inputs (empty, whitespace, extra keys) do not crash the engine."""
    payload = {
        "productId": "PROD-BOUND-01",
        "productName": "   ",
        "isImported": False,
        "manufacturerName": "",
        "manufacturerAddress": "   ",
        "netQuantity": "",
        "mrp": "   ",
        "extraUnusedKey": "should be ignored gracefully"
    }
    res = client.post("/api/rules/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["overallStatus"] == "FAIL"
    assert data["failedRules"] >= 3
