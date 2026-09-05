from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.schemas.scan_schemas import (
    ProductFields,
    Violation,
    ComplianceResult,
    ScanResponse,
    ScanListResponse,
    ErrorResponse,
)


def test_direct_scan_response_construction():
    now = datetime.now(timezone.utc)
    product = ProductFields(
        product_name="Sample Biscuit",
        manufacturer="Sample Foods Ltd",
        net_quantity="100g",
        mrp="Rs. 20",
        batch_number="B001",
        mfg_date="2026-02-01",
        consumer_care="support@sample.com",
    )
    violation = Violation(
        rule="RULE_NET_QTY",
        description="Net quantity missing unit",
        field="net_quantity",
    )
    compliance = ComplianceResult(
        status="NON_COMPLIANT",
        violations=[violation],
    )
    response = ScanResponse(
        scan_id="test-uuid-1234",
        timestamp=now,
        product=product,
        extracted_fields={"raw_ocr": "Sample Biscuit 100g"},
        compliance=compliance,
        image_ref="/uploads/biscuit.jpg",
    )

    assert response.scan_id == "test-uuid-1234"
    assert response.product.product_name == "Sample Biscuit"
    assert response.compliance.status == "NON_COMPLIANT"
    assert len(response.compliance.violations) == 1
    assert response.compliance.violations[0].rule == "RULE_NET_QTY"


def test_from_db_row_conversion():
    flat_db_row = {
        "scan_id": "scan-8888-9999",
        "timestamp": "2026-08-23T12:00:00+00:00",
        "product_name": "Test Juice",
        "manufacturer": "Beverage Co",
        "net_quantity": "1L",
        "mrp": "Rs. 99",
        "batch_number": "J100",
        "mfg_date": "2026-05-10",
        "consumer_care": "help@bevco.com",
        "extracted_fields": {"brand": "Test Juice", "volume": "1L"},
        "compliance_status": "COMPLIANT",
        "violations": [
            {
                "rule": "RULE_MRP",
                "description": "MRP format verified",
                "field": "mrp",
            }
        ],
        "image_ref": "images/juice.png",
    }

    scan_response = ScanResponse.from_db_row(flat_db_row)

    assert scan_response.scan_id == "scan-8888-9999"
    assert scan_response.product.product_name == "Test Juice"
    assert scan_response.product.manufacturer == "Beverage Co"
    assert scan_response.product.net_quantity == "1L"
    assert scan_response.product.mrp == "Rs. 99"
    assert scan_response.extracted_fields == {"brand": "Test Juice", "volume": "1L"}
    assert scan_response.compliance.status == "COMPLIANT"
    assert len(scan_response.compliance.violations) == 1
    assert scan_response.compliance.violations[0].rule == "RULE_MRP"
    assert scan_response.image_ref == "images/juice.png"


def test_invalid_compliance_status_raises_validation_error():
    flat_db_row = {
        "scan_id": "scan-0000",
        "timestamp": "2026-08-23T12:00:00+00:00",
        "product_name": "Test Item",
        "compliance_status": "INVALID_STATUS",  # Not COMPLIANT, NON_COMPLIANT, or PARTIAL
        "violations": [],
        "image_ref": "test.jpg",
    }

    with pytest.raises(ValidationError):
        ScanResponse.from_db_row(flat_db_row)
