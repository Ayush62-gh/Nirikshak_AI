"""
API-level tests for v1 Compliance Engine REST Endpoints.
Verifies HTTP status handling, request schemas, validation error formats, CORS, and engine parity.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.models.product import EvaluateProductRequest
from app.core.engine import RuleEngine

client = TestClient(app)


def test_api_v1_health_endpoint():
    """Test 1: GET /health and GET /api/v1/health return HTTP 200 OK and healthy status."""
    res1 = client.get("/health")
    assert res1.status_code == 200
    assert res1.json()["status"] == "healthy"

    res2 = client.get("/api/v1/health")
    assert res2.status_code == 200
    assert res2.json()["status"] == "healthy"


def test_api_v1_compliance_check_pass():
    """Test 2: POST /api/v1/compliance/check with valid payload returns HTTP 200 and PASS overall status."""
    payload = {
        "productId": "PROD-API-01",
        "productName": "Organic Earl Grey Tea",
        "isImported": False,
        "manufacturerName": "Himalayan Tea Estates Pvt Ltd",
        "manufacturerAddress": "Factory 4, Darjeeling - 734101",
        "netQuantity": "250 g",
        "mrp": "Rs. 450.00 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@himalayantea.com"
    }
    response = client.post("/api/v1/compliance/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["productId"] == "PROD-API-01"
    assert data["overallStatus"] == "PASS"
    assert data["failedRules"] == 0
    assert data["manualReviewRules"] == 0
    assert "decisionTrace" in data


def test_api_v1_compliance_check_fail():
    """Test 3: Legally non-compliant product returns HTTP 200 OK with overallStatus = FAIL."""
    payload = {
        "productId": "PROD-API-02",
        "productName": "Green Tea",
        "isImported": False,
        "manufacturerName": "Tea Co",
        "manufacturerAddress": "Noida",
        "netQuantity": "100 g",
        "mrp": None  # Missing MRP -> FAIL
    }
    response = client.post("/api/v1/compliance/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["productId"] == "PROD-API-02"
    assert data["overallStatus"] == "FAIL"
    assert data["failedRules"] >= 1


def test_api_v1_compliance_check_manual_review():
    """Test 4: Product needing manual review returns HTTP 200 OK with overallStatus = MANUAL_REVIEW."""
    payload = {
        "productId": "PROD-API-03",
        "productName": "Green Tea",
        "isImported": False,
        "manufacturerName": "Tea Co",
        "manufacturerAddress": "Noida",
        "netQuantity": "100 g",
        "mrp": "350",  # Unverified tax clause -> MANUAL_REVIEW
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@teaco.com"
    }
    response = client.post("/api/v1/compliance/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["productId"] == "PROD-API-03"
    assert data["overallStatus"] == "MANUAL_REVIEW"


def test_api_v1_compliance_check_not_applicable():
    """Test 5: Domestic product correctly returns NOT_APPLICABLE for importer rule."""
    payload = {
        "productId": "PROD-API-04",
        "productName": "Domestic Herbal Soap",
        "isImported": False,
        "manufacturerName": "Soap Makers Ltd",
        "manufacturerAddress": "Haridwar",
        "netQuantity": "125 g",
        "mrp": "Rs. 60.00 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@soap.in"
    }
    response = client.post("/api/v1/compliance/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    imp_rule = next(r for r in data["individualRuleResults"] if r["ruleId"] == "LM-RULE-IMP-003")
    assert imp_rule["status"] == "NOT_APPLICABLE"


def test_api_v1_malformed_input_validation_error():
    """Test 6: Invalid JSON data type returns HTTP 400 Bad Request with standardized error structure."""
    payload = {
        "productId": 12345,  # Unexpected non-string or malformed field
        "isImported": "not_a_boolean"  # Invalid boolean type
    }
    response = client.post("/api/v1/compliance/check", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert len(data["error"]["details"]) > 0


def test_api_v1_missing_request_body():
    """Test 7: Missing request body returns HTTP 400 Bad Request."""
    response = client.post("/api/v1/compliance/check")
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_api_v1_end_to_end_parity_with_engine():
    """Test 8: End-to-end integration test verifying HTTP API response matches direct Compliance Engine result."""
    payload_dict = {
        "productId": "PROD-API-PARITY",
        "productName": "Parity Test Commodity",
        "isImported": False,
        "manufacturerName": "Parity Maker Pvt Ltd",
        "manufacturerAddress": "Sector 62, Noida - 201301",
        "netQuantity": "500 ml",
        "mrp": "Rs. 199.00 (incl. of all taxes)",
        "monthOfPacking": "08",
        "yearOfPacking": "2026",
        "consumerCare": "care@parity.com"
    }

    # Direct Engine Evaluation
    engine = RuleEngine()
    req_obj = EvaluateProductRequest(**payload_dict)
    direct_report = engine.evaluate(req_obj)

    # API Evaluation
    api_response = client.post("/api/v1/compliance/check", json=payload_dict)
    assert api_response.status_code == 200
    api_report_dict = api_response.json()

    # Verify complete parity
    assert api_report_dict["productId"] == direct_report.productId
    assert api_report_dict["overallStatus"] == direct_report.overallStatus
    assert api_report_dict["totalRules"] == direct_report.totalRules
    assert api_report_dict["passedRules"] == direct_report.passedRules
    assert api_report_dict["failedRules"] == direct_report.failedRules
    assert api_report_dict["manualReviewRules"] == direct_report.manualReviewRules
