import os
import pytest
from app.db.session import init_db, save_scan, get_scan, list_scans


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_save_get_and_list_scans():
    sample_scan = {
        "product_name": "Test Milk Powder",
        "manufacturer": "Nirikshak Foods Ltd",
        "net_quantity": "500g",
        "mrp": "Rs. 250",
        "batch_number": "BATCH123",
        "mfg_date": "2026-01-01",
        "consumer_care": "care@nirikshak.com",
        "extracted_fields": {"raw_ocr": "Test Milk Powder 500g Rs. 250"},
        "compliance_status": "COMPLIANT",
        "violations": [],
        "image_ref": "/uploads/test_image.jpg",
    }

    # 1. Save scan
    scan_id = save_scan(sample_scan)
    assert isinstance(scan_id, str)
    assert len(scan_id) > 0

    # 2. Get scan and verify data matches
    retrieved_scan = get_scan(scan_id)
    assert retrieved_scan is not None
    assert isinstance(retrieved_scan, dict)
    assert retrieved_scan["scan_id"] == scan_id
    assert retrieved_scan["product_name"] == "Test Milk Powder"
    assert retrieved_scan["manufacturer"] == "Nirikshak Foods Ltd"
    assert retrieved_scan["net_quantity"] == "500g"
    assert retrieved_scan["mrp"] == "Rs. 250"
    assert retrieved_scan["compliance_status"] == "COMPLIANT"
    assert retrieved_scan["extracted_fields"] == {"raw_ocr": "Test Milk Powder 500g Rs. 250"}

    # 3. List scans and verify saved scan is in results
    scans_list = list_scans(page=1, limit=10)
    assert isinstance(scans_list, list)
    scan_ids = [s["scan_id"] for s in scans_list]
    assert scan_id in scan_ids
