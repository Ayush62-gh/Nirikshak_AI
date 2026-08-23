from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pytesseract
from PIL import Image

from app.core.config import settings
from app.core.exceptions import OCRProcessingError
from app.core.logging import logger
from app.services.image_service import ImageService
from app.utils.file_utils import get_absolute_path
from app.utils.text_utils import clean_ocr_text


@dataclass
class OCRBoundingBox:
    x: int
    y: int
    w: int
    h: int

    def to_dict(self) -> Dict[str, int]:
        return {"x": self.x, "y": self.y, "w": self.w, "h": self.h}


@dataclass
class OCRTextBlock:
    text: str
    confidence: float
    bbox: Optional[OCRBoundingBox] = None


@dataclass
class OCRResult:
    full_text: str
    blocks: List[OCRTextBlock] = field(default_factory=list)
    mean_confidence: float = 0.0
    provider_name: str = "tesseract"
    image_path: str = ""


class OCRProvider(ABC):
    """Abstract interface for pluggable OCR engines (Tesseract, Google Vision, Azure, AWS)."""

    @abstractmethod
    async def extract_text(self, image_path: Union[str, Path]) -> OCRResult:
        """Extract text and bounding boxes from an image."""
        pass


class TesseractOCRProvider(OCRProvider):
    """Local Tesseract OCR implementation with image preprocessing."""

    def __init__(self, tesseract_cmd: Optional[str] = None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        elif settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

    async def extract_text(self, image_path: Union[str, Path]) -> OCRResult:
        abs_path = get_absolute_path(str(image_path))
        if not abs_path.exists():
            raise OCRProcessingError(f"Image not found at {abs_path}")

        try:
            # 1. Preprocess image with OpenCV
            preprocessed_img, preproc_path = ImageService.preprocess_image_for_ocr(
                abs_path
            )

            # 2. Extract detailed OCR data (words, confidence, bounding boxes)
            data = pytesseract.image_to_data(
                preprocessed_img, output_type=pytesseract.Output.DICT
            )

            blocks: List[OCRTextBlock] = []
            confidences: List[float] = []
            extracted_words: List[str] = []

            n_boxes = len(data["text"])
            for i in range(n_boxes):
                word = data["text"][i].strip()
                conf_str = data["conf"][i]

                try:
                    conf = float(conf_str)
                except (ValueError, TypeError):
                    conf = -1.0

                if conf > 0 and word:
                    norm_conf = round(conf / 100.0, 2)
                    confidences.append(norm_conf)
                    extracted_words.append(word)

                    bbox = OCRBoundingBox(
                        x=int(data["left"][i]),
                        y=int(data["top"][i]),
                        w=int(data["width"][i]),
                        h=int(data["height"][i]),
                    )
                    blocks.append(
                        OCRTextBlock(text=word, confidence=norm_conf, bbox=bbox)
                    )

            # Full raw text
            raw_text = pytesseract.image_to_string(preprocessed_img)
            cleaned = clean_ocr_text(raw_text)

            mean_conf = (
                round(sum(confidences) / len(confidences), 2) if confidences else 0.0
            )

            return OCRResult(
                full_text=cleaned,
                blocks=blocks,
                mean_confidence=mean_conf,
                provider_name="tesseract",
                image_path=str(image_path),
            )

        except pytesseract.TesseractNotFoundError:
            logger.warning(
                "Tesseract binary not found in system PATH. Falling back to Mock Provider output for testing."
            )
            mock = MockOCRProvider()
            return await mock.extract_text(image_path)
        except Exception as e:
            logger.error(f"Tesseract OCR failed on {image_path}: {e}")
            raise OCRProcessingError(f"OCR execution failed: {str(e)}")


class MockOCRProvider(OCRProvider):
    """Mock OCR provider for unit tests and environments without Tesseract binary."""

    def __init__(self, custom_text: Optional[str] = None):
        self.custom_text = custom_text

    async def extract_text(self, image_path: Union[str, Path]) -> OCRResult:
        default_sample = (
            "NIRIKSHAK PACKAGED SNACKS\n"
            "Manufactured by: Pure Naturals Foodworks Pvt. Ltd.\n"
            "Reg. Office: Plot 42, Industrial Area, Sector 62, Noida, Uttar Pradesh - 201301\n"
            "Packed by: Pure Naturals Foodworks Pvt. Ltd., Noida 201301\n"
            "Net Qty: 200 g\n"
            "MRP Rs. 85.00 (incl. of all taxes)\n"
            "Unit Sale Price: Rs. 0.425 / g\n"
            "Mfg. Date: 08/2026\n"
            "Best Before: 6 Months from Packaging\n"
            "Consumer Care Cell: Pure Naturals Foodworks, Plot 42, Noida\n"
            "Toll Free No: 1800-123-4567\n"
            "Email: customercare@purenaturals.com\n"
            "Country of Origin: India\n"
        )
        text = self.custom_text or default_sample
        return OCRResult(
            full_text=text,
            blocks=[
                OCRTextBlock(
                    text="MRP Rs. 85.00 (incl. of all taxes)",
                    confidence=0.95,
                    bbox=OCRBoundingBox(x=10, y=100, w=200, h=30),
                ),
                OCRTextBlock(
                    text="Net Qty: 200 g",
                    confidence=0.98,
                    bbox=OCRBoundingBox(x=10, y=140, w=120, h=25),
                ),
            ],
            mean_confidence=0.96,
            provider_name="mock",
            image_path=str(image_path),
        )


def get_ocr_provider(provider_name: Optional[str] = None) -> OCRProvider:
    """Factory function for selecting active OCR provider."""
    name = (provider_name or settings.OCR_PROVIDER).lower()

    if name == "mock":
        return MockOCRProvider()
    elif name == "tesseract":
        return TesseractOCRProvider()
    else:
        logger.warning(
            f"Unknown OCR provider '{name}', defaulting to Tesseract OCR provider"
        )
        return TesseractOCRProvider()
