from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class ProductFields(BaseModel):
    product_name: str | None = None
    manufacturer: str | None = None
    net_quantity: str | None = None
    mrp: str | None = None
    batch_number: str | None = None
    mfg_date: str | None = None
    consumer_care: str | None = None


class Violation(BaseModel):
    rule: str
    description: str
    field: str


class ComplianceResult(BaseModel):
    status: Literal["COMPLIANT", "NON_COMPLIANT", "PARTIAL"]
    violations: list[Violation] = Field(default_factory=list)


class ScanResponse(BaseModel):
    scan_id: str
    timestamp: datetime
    product: ProductFields
    extracted_fields: dict = Field(default_factory=dict)
    compliance: ComplianceResult
    image_ref: str

    @classmethod
    def from_db_row(cls, row: dict) -> "ScanResponse":
        product = ProductFields(
            product_name=row.get("product_name"),
            manufacturer=row.get("manufacturer"),
            net_quantity=row.get("net_quantity"),
            mrp=row.get("mrp"),
            batch_number=row.get("batch_number"),
            mfg_date=row.get("mfg_date"),
            consumer_care=row.get("consumer_care"),
        )

        raw_violations = row.get("violations") or []
        violations = [
            v if isinstance(v, Violation) else Violation(**v) for v in raw_violations
        ]

        compliance = ComplianceResult(
            status=row.get("compliance_status", "PARTIAL"),
            violations=violations,
        )

        return cls(
            scan_id=row["scan_id"],
            timestamp=row["timestamp"],
            product=product,
            extracted_fields=row.get("extracted_fields") or {},
            compliance=compliance,
            image_ref=row.get("image_ref") or "",
        )


class ScanListResponse(BaseModel):
    scans: list[ScanResponse]
    page: int
    limit: int
    total: int


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
