from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.inspection import ComplianceResultStatus, InspectionStatus
from app.schemas.declaration import DeclarationResponse
from app.schemas.product import ProductResponse
from app.schemas.violation import ViolationResponse


class InspectionCreate(BaseModel):
    product_id: Optional[int] = Field(default=None, description="Existing product ID (if known)")
    product_name: Optional[str] = Field(default=None, description="Product name if creating with new product")
    barcode: Optional[str] = Field(default=None, description="Product barcode")
    category: Optional[str] = Field(default=None, description="Product category")
    manufacturer: Optional[str] = Field(default=None, description="Product manufacturer")


class InspectionImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inspection_id: int
    image_path: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    uploaded_at: datetime


class InspectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: Optional[int]
    inspector_id: int
    inspection_date: datetime
    status: InspectionStatus
    compliance_score: Optional[float]
    overall_result: ComplianceResultStatus
    created_at: datetime
    updated_at: datetime
    product: Optional[ProductResponse] = None


class InspectionDetailResponse(InspectionResponse):
    images: List[InspectionImageResponse] = []
    declarations: List[DeclarationResponse] = []
    violations: List[ViolationResponse] = []
