"""
Data Transfer Objects (DTOs) for Structured Product Input Data.
"""

from typing import Dict, Optional, Any, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.rule_result import RuleEvidence, EvidenceSource


class DeclarationField(BaseModel):
    """Represents an extracted/provided mandatory declaration label field on a packaged commodity."""
    value: Optional[str] = Field(None, description="Raw text value of the declaration")
    confidence: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Extraction/Data confidence score")
    is_present: bool = Field(True, description="Whether the declaration label is present on the package")


class ProductData(BaseModel):
    """
    Structured Product Data model matching Legal Metrology (Packaged Commodities) Rules requirement inputs.
    """
    product_id: str = Field(..., description="Unique product SKU or identifier")
    product_name: str = Field(..., description="Generic name or description of commodity")
    category: str = Field("general", description="Product category (e.g., food, cosmetics, electronics, general)")
    net_quantity: Optional[str] = Field(None, description="Declared Net Quantity (e.g., 500 g, 1 L, 5 units)")
    mrp: Optional[str] = Field(None, description="Maximum Retail Price declaration (e.g., Rs. 250.00 incl. of all taxes)")
    manufacturer_details: Optional[str] = Field(None, description="Name and address of Manufacturer / Packer / Importer")
    country_of_origin: Optional[str] = Field(None, description="Country of Origin declaration")
    consumer_care_details: Optional[str] = Field(None, description="Customer care contact details")
    month_year_of_manufacture: Optional[str] = Field(None, description="Month & Year of manufacture / packing / import")
    additional_declarations: Dict[str, Any] = Field(default_factory=dict, description="Custom or specific metadata fields")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": "PROD-10293",
                "product_name": "Premium Organic Green Tea",
                "category": "food",
                "net_quantity": "100 g",
                "mrp": "Rs. 350.00 (Incl. of all taxes)",
                "manufacturer_details": "Tea Co Pvt Ltd, Industrial Area, Sector 5, New Delhi - 110001",
                "country_of_origin": "India",
                "consumer_care_details": "Email: care@teaco.com, Tel: 1800-123-4567",
                "month_year_of_manufacture": "07/2026",
                "additional_declarations": {}
            }
        }
    )


class EvaluateProductRequest(BaseModel):
    """
    API Contract Request payload from Teammates' Backend / Upstream Services.
    Supports flexible structured product inputs regardless of origin (OCR, AI, Manual, Integration).
    """
    productId: str = Field(..., description="Unique product identifier or SKU")
    productName: Optional[str] = Field(None, description="Brand name or generic name of commodity")
    productType: Optional[str] = Field(None, description="Category/type (e.g., food, cosmetics, electronics)")
    isImported: Optional[bool] = Field(None, description="Whether the commodity is imported into India (True=Imported, False=Domestic, None=Unconfirmed)")
    manufacturerName: Optional[str] = Field(None, description="Name of the Manufacturer")
    manufacturerAddress: Optional[str] = Field(None, description="Complete address of the Manufacturer")
    packerName: Optional[str] = Field(None, description="Name of the Packer (if different from manufacturer)")
    importerName: Optional[str] = Field(None, description="Name of the Importer (mandatory for imported packages)")
    netQuantity: Optional[str] = Field(None, description="Declared Net Quantity (e.g., 500 g, 1 L, 10 N)")
    mrp: Optional[str] = Field(None, description="Declared Maximum Retail Price (e.g., Rs. 250.00 incl. of all taxes)")
    monthOfPacking: Optional[str] = Field(None, description="Month of packing/manufacture (e.g., '07' or 'July')")
    yearOfPacking: Optional[str] = Field(None, description="Year of packing/manufacture (e.g., '2026')")
    consumerCare: Optional[str] = Field(None, description="Consumer care email, phone, or address details")
    countryOfOrigin: Optional[str] = Field(None, description="Country of Origin (mandatory for imported goods)")
    fieldEvidence: Optional[Dict[str, RuleEvidence]] = Field(default_factory=dict, description="Optional metadata map connecting fields to RuleEvidence provenance")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "productId": "PROD-88210",
                "productName": "Organic Herbal Green Tea",
                "productType": "food",
                "isImported": False,
                "manufacturerName": "Ayurveda Organics Pvt Ltd",
                "manufacturerAddress": "Plot 12, Industrial Estate, Haridwar, Uttarakhand - 249401",
                "packerName": None,
                "importerName": None,
                "netQuantity": "100 g",
                "mrp": "Rs. 299.00 (incl. of all taxes)",
                "monthOfPacking": "08",
                "yearOfPacking": "2026",
                "consumerCare": "Email: care@ayurvedaorganics.com, Tel: 1800-888-9999",
                "countryOfOrigin": "India"
            }
        }
    )

