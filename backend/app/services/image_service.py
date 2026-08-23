import os
from pathlib import Path
from typing import Optional, Tuple, Union
import cv2
import numpy as np
from PIL import Image, ImageOps

from app.core.exceptions import OCRProcessingError
from app.core.logging import logger
from app.utils.file_utils import get_absolute_path


class ImageService:
    """Provides computer vision preprocessing pipeline for packaged commodity images."""

    @staticmethod
    def load_image(image_path: Union[str, Path]) -> np.ndarray:
        """Load image from disk into OpenCV BGR format with proper orientation."""
        abs_path = get_absolute_path(str(image_path))
        if not abs_path.exists():
            raise OCRProcessingError(f"Image file does not exist at {abs_path}")

        try:
            # First use PIL to handle EXIF orientation properly
            with Image.open(abs_path) as pil_img:
                pil_img = ImageOps.exif_transpose(pil_img)
                if pil_img.mode != "RGB":
                    pil_img = pil_img.convert("RGB")
                img_rgb = np.array(pil_img)
                # Convert RGB to BGR for OpenCV
                img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
                return img_bgr
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            raise OCRProcessingError(f"Unable to decode image: {str(e)}")

    @staticmethod
    def resize_for_ocr(image: np.ndarray, min_dimension: int = 1200, max_dimension: int = 3000) -> np.ndarray:
        """Resize image to an optimal resolution range for OCR text recognition."""
        h, w = image.shape[:2]
        max_dim = max(h, w)
        min_dim = min(h, w)

        if min_dim < min_dimension:
            scale = min_dimension / min_dim
            new_w = int(w * scale)
            new_h = int(h * scale)
            return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        elif max_dim > max_dimension:
            scale = max_dimension / max_dim
            new_w = int(w * scale)
            new_h = int(h * scale)
            return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

        return image

    @staticmethod
    def to_grayscale(image: np.ndarray) -> np.ndarray:
        """Convert BGR image to single channel grayscale."""
        if len(image.shape) == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def enhance_contrast(gray_image: np.ndarray) -> np.ndarray:
        """Apply Contrast Limited Adaptive Histogram Equalization (CLAHE)."""
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray_image)

    @staticmethod
    def denoise(gray_image: np.ndarray) -> np.ndarray:
        """Reduce high frequency noise while preserving label text edges."""
        return cv2.bilateralFilter(gray_image, d=7, sigmaColor=50, sigmaSpace=50)

    @staticmethod
    def binarize(gray_image: np.ndarray) -> np.ndarray:
        """Apply Otsu adaptive thresholding for crisp text characters."""
        _, thresh = cv2.threshold(
            gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        return thresh

    @staticmethod
    def preprocess_image_for_ocr(
        image_path: Union[str, Path], save_debug: bool = False
    ) -> Tuple[np.ndarray, str]:
        """
        Execute full preprocessing pipeline on packaged product image.
        Returns (preprocessed_opencv_image, path_to_processed_file).
        """
        img = ImageService.load_image(image_path)
        img_resized = ImageService.resize_for_ocr(img)
        gray = ImageService.to_grayscale(img_resized)
        denoised = ImageService.denoise(gray)
        enhanced = ImageService.enhance_contrast(denoised)

        processed_path = ""
        if save_debug or True:
            # Save preprocessed image next to original for inspection / OCR ingestion
            original_abs = get_absolute_path(str(image_path))
            preprocessed_filename = f"preproc_{original_abs.stem}.png"
            preproc_dest = original_abs.parent / preprocessed_filename
            cv2.imwrite(str(preproc_dest), enhanced)
            processed_path = str(preproc_dest)

        return enhanced, processed_path
