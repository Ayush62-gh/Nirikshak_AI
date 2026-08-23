from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class DeclarationBase(BaseModel):
    declaration_type: str = Field(..., description="Type of declaration (e.g. mrp, net_quantity, mfg_date, manufacturer)")
    extracted_value: Optional[str] = Field(default=None, description="Raw OCR extracted string")
    normalized_value: Optional[str] = Field(default=None, description="Cleaned, standardized value")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="OCR/NLP extraction confidence score")
    source_image: Optional[str] = Field(default=None, description="Relative path of source image")
    bounding_box: Optional[Dict[str, Any]] = Field(default=None, description="Coordinates bounding box [x, y, w, h]")
    is_valid: bool = Field(default=True, description="Whether extracted value matches standard format")


class DeclarationCreate(DeclarationBase):
    inspection_id: int


class DeclarationResponse(DeclarationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inspection_id: int
    created_at: datetime
