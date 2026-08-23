import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    User,
    UserRole,
    Product,
    Inspection,
    InspectionImage,
    InspectionStatus,
    ComplianceResultStatus,
    Declaration,
    Violation,
    ViolationSeverity,
    ViolationStatus,
    Rule,
    Report,
    AuditLog,
)


@pytest.mark.asyncio
async def test_create_and_query_models(db_session: AsyncSession):
    """Verify that all models can be created, persisted, and queried with relationships."""
    
    # 1. Create User
    user = User(
        name="Officer Rajesh Kumar",
        email="rajesh.kumar@metrology.gov.in",
        password_hash="hashed_secret_password",
        role=UserRole.INSPECTOR,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    assert user.id is not None
    assert user.role == UserRole.INSPECTOR

    # 2. Create Product
    product = Product(
        product_name="Organic Almond Milk 1L",
        barcode="8901234567890",
        category="Beverages",
        manufacturer="Pure Organics Pvt Ltd",
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    assert product.id is not None

    # 3. Create Inspection
    inspection = Inspection(
        product_id=product.id,
        inspector_id=user.id,
        status=InspectionStatus.PROCESSING,
        compliance_score=85.5,
        overall_result=ComplianceResultStatus.NON_COMPLIANT,
    )
    db_session.add(inspection)
    await db_session.commit()
    await db_session.refresh(inspection)
    assert inspection.id is not None

    # 4. Create Inspection Image
    image = InspectionImage(
        inspection_id=inspection.id,
        image_path="uploads/test_sample_01.jpg",
        original_filename="sample_front_label.jpg",
        file_size_bytes=102400,
        mime_type="image/jpeg",
    )
    db_session.add(image)

    # 5. Create Declaration
    declaration = Declaration(
        inspection_id=inspection.id,
        declaration_type="mrp",
        extracted_value="MRP Rs. 150.00 (incl. of all taxes)",
        normalized_value="150.00 INR",
        confidence=0.96,
        is_valid=True,
    )
    db_session.add(declaration)

    # 6. Create Rule
    rule = Rule(
        rule_id="LM-PC-001",
        rule_number="Rule 6(1)(e)",
        rule_name="Mandatory MRP Declaration",
        category="MRP",
        description="Every package shall bear MRP inclusive of all taxes.",
        requirement="MRP must be clearly declared with 'inclusive of all taxes'.",
        validation_type="presence_and_format",
        severity="HIGH",
        active=True,
        version="2011",
    )
    db_session.add(rule)

    # 7. Create Violation
    violation = Violation(
        inspection_id=inspection.id,
        rule_id="LM-PC-002",
        violation_type="MISSING_CONSUMER_CARE_EMAIL",
        description="Consumer care email address missing on package label.",
        severity=ViolationSeverity.HIGH,
        status=ViolationStatus.OPEN,
    )
    db_session.add(violation)

    # 8. Create Report
    report = Report(
        inspection_id=inspection.id,
        report_path="reports/inspection_report_001.pdf",
        report_type="PDF",
    )
    db_session.add(report)

    # 9. Create Audit Log
    audit = AuditLog(
        user_id=user.id,
        action="INSPECTION_CREATED",
        entity_type="INSPECTION",
        entity_id=str(inspection.id),
        metadata_json={"ip": "127.0.0.1"},
    )
    db_session.add(audit)

    await db_session.commit()

    # Query Inspection with declarations and violations
    result = await db_session.execute(
        select(Inspection).where(Inspection.id == inspection.id)
    )
    saved_inspection = result.scalar_one()
    assert saved_inspection.inspector_id == user.id
    assert saved_inspection.compliance_score == 85.5
