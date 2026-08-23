from pathlib import Path
import numpy as np
import pytest
from PIL import Image

from app.services.image_service import ImageService
from app.services.ocr_service import MockOCRProvider, OCRResult, get_ocr_provider
from app.services.extraction_service import DeclarationExtractor


def test_image_preprocessing_pipeline(tmp_path: Path):
    """Test image loading, resizing, grayscale conversion, and contrast enhancement."""
    # Create test synthetic image
    test_img_path = tmp_path / "test_label.png"
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    img.save(test_img_path)

    # 1. Load image
    loaded_img = ImageService.load_image(test_img_path)
    assert isinstance(loaded_img, np.ndarray)
    assert len(loaded_img.shape) == 3

    # 2. Resizing
    resized = ImageService.resize_for_ocr(loaded_img, min_dimension=1200)
    assert min(resized.shape[:2]) >= 1200

    # 3. Grayscale
    gray = ImageService.to_grayscale(resized)
    assert len(gray.shape) == 2

    # 4. Contrast enhancement & Denoise
    enhanced = ImageService.enhance_contrast(gray)
    denoised = ImageService.denoise(enhanced)
    assert denoised.shape == gray.shape


@pytest.mark.asyncio
async def test_ocr_provider_abstraction(tmp_path: Path):
    """Verify that Mock and extensible OCR providers adhere to the contract."""
    test_img_path = tmp_path / "label.jpg"
    img = Image.new("RGB", (400, 300), color=(255, 255, 255))
    img.save(test_img_path)

    provider = MockOCRProvider()
    result = await provider.extract_text(test_img_path)

    assert isinstance(result, OCRResult)
    assert "MRP" in result.full_text
    assert result.mean_confidence > 0.8
    assert len(result.blocks) > 0


def test_declaration_extractor_comprehensive():
    """Test declaration extraction across all required Legal Metrology fields."""
    sample_ocr_text = (
        "DELICIOUS POTATO CHIPS\n"
        "Manufactured by: Sunshine Foods India Pvt Ltd, Plot 10, Sector 5, Haridwar, Uttarakhand - 249403\n"
        "Packed by: Sunshine Foods India Pvt Ltd, Haridwar\n"
        "Net Qty: 150 gm\n"
        "MRP Rs. 50.00 (incl. of all taxes)\n"
        "Mfg. Date: 07/2026\n"
        "Best Before: 9 Months from date of packaging\n"
        "Customer Care Executive: Sunshine Foods, Haridwar\n"
        "Toll Free: 1800-987-6543\n"
        "Email: feedback@sunshinefoods.in\n"
        "Country of Origin: India\n"
    )

    ocr_result = OCRResult(
        full_text=sample_ocr_text,
        blocks=[],
        mean_confidence=0.95,
        provider_name="mock",
        image_path="uploads/test.jpg",
    )

    declarations = DeclarationExtractor.extract_all(ocr_result)
    dec_dict = {d.declaration_type: d for d in declarations}

    # 1. Verify MRP
    assert "mrp" in dec_dict
    assert "50.00" in dec_dict["mrp"].extracted_value
    assert dec_dict["mrp"].is_valid is True

    # 2. Verify Net Quantity & unit standardization
    assert "net_quantity" in dec_dict
    assert dec_dict["net_quantity"].normalized_value == "150 g"
    assert dec_dict["net_quantity"].is_valid is True

    # 3. Verify Dates
    assert "mfg_date" in dec_dict
    assert dec_dict["mfg_date"].normalized_value == "07/2026"
    assert "expiry_date" in dec_dict

    # 4. Verify Manufacturer & PIN code detection
    assert "manufacturer" in dec_dict
    assert "249403" in dec_dict["manufacturer"].extracted_value

    # 5. Verify Consumer Care Email and Phone
    assert "consumer_care_email" in dec_dict
    assert dec_dict["consumer_care_email"].normalized_value == "feedback@sunshinefoods.in"
    assert "consumer_care_phone" in dec_dict
    assert "18009876543" in dec_dict["consumer_care_phone"].normalized_value

    # 6. Verify Country of Origin
    assert "country_of_origin" in dec_dict
    assert dec_dict["country_of_origin"].normalized_value == "India"


def test_declaration_extractor_mrp_without_tax():
    """Verify that an MRP declaration without 'incl. of all taxes' is flagged as invalid."""
    ocr_text = "Net Qty: 500 ml\nMRP Rs. 120.00\nMfg Date: 05/2026\n"
    ocr_result = OCRResult(full_text=ocr_text, image_path="uploads/item.jpg")

    declarations = DeclarationExtractor.extract_all(ocr_result)
    dec_dict = {d.declaration_type: d for d in declarations}

    assert "mrp" in dec_dict
    assert dec_dict["mrp"].is_valid is False  # Missing tax inclusive declaration
