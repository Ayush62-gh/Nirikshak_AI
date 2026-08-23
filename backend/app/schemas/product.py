from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=255, description="Name or title of packaged product")
    barcode: Optional[str] = Field(default=None, max_length=100, description="EAN/UPC barcode number")
    category: Optional[str] = Field(default=None, max_length=100, description="Product category (e.g. Food, Cosmetics, Electronics)")
    manufacturer: Optional[str] = Field(default=None, max_length=255, description="Registered manufacturer name")


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    product_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    barcode: Optional[str] = Field(default=None, max_length=100)
    category: Optional[str] = Field(default=None, max_length=100)
    manufacturer: Optional[str] = Field(default=None, max_length=255)


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
