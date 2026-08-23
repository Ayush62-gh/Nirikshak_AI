# NIRIKSHAK AI — OCR and Image Processing Module

This module processes packaged-product label images and extracts English
and Hindi text using EasyOCR.

It is a part of NIRIKSHAK AI, a system intended to identify possible
packaged-commodity label compliance issues.

This module does not make legal-compliance decisions. It only returns
image-quality information, extracted text, confidence scores and
text-box coordinates. A separate rule engine uses this output.

## Features

- Reads product images from image paths
- Handles missing, corrupt and unsupported images
- Corrects EXIF orientation
- Resizes large images while preserving aspect ratio
- Measures blur and brightness
- Assigns `ACCEPTABLE`, `POOR` or `UNREADABLE` quality status
- Converts images to grayscale
- Reduces image noise
- Improves local contrast using CLAHE
- Attempts small-angle tilt correction
- Extracts English and Hindi text using EasyOCR
- Returns confidence scores and bounding-box coordinates
- Saves processed images
- Generates annotated images with detected text boxes
- Supports multiple images belonging to the same product
- Returns JSON-serializable Python dictionaries
- Can later be imported into a FastAPI backend

## Technology

- Python 3.10 or 3.11
- OpenCV
- EasyOCR
- Pillow
- NumPy
- PyTorch
- Pytest

## Folder Structure

```text
ml_service/
├── input_images/          Local product-label images
├── processed_images/      Generated enhanced images
├── annotated_images/      Generated OCR-box images
├── tests/
│   └── test_ocr.py
├── image_processor.py     Complete integration pipeline
├── ocr.py                 OCR and annotation functions
├── preprocess.py          Image preprocessing functions
├── quality_checker.py     Blur and brightness checking
├── requirements.txt
├── .gitignore
└── README.md
```

Local input images and generated images are ignored by Git.

## Environment Setup

Python 3.10 or Python 3.11 is recommended.

Check installed Python versions:

```powershell
py -0p
```

Create a virtual environment:

```powershell
py -3.11 -m venv venv
```

### Activate in Windows PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

If script execution is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### Activate in Windows Command Prompt

```bat
venv\Scripts\activate.bat
```

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

For a CPU-only Windows setup, PyTorch can be installed first with:

```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

Install the remaining requirements:

```powershell
pip install -r requirements.txt
```

## Single-Image Processing

Place a product image inside `input_images`.

Example:

```text
input_images/catch_label.jpg
```

Run the complete pipeline:

```powershell
python .\image_processor.py ".\input_images\catch_label.jpg"
```

The result includes:

- Original-image quality
- Extracted full text
- Individual OCR text blocks
- Confidence scores
- Bounding-box coordinates
- Processed-image path
- Annotated-image path

## Required Python Function

```python
from image_processor import process_product_image

result = process_product_image(
    "input_images/catch_label.jpg"
)
```

Successful result format:

```python
{
    "quality": {
        "blur_score": 125.4,
        "is_blurry": False,
        "brightness": 142.0,
        "quality_status": "ACCEPTABLE"
    },
    "full_text": "MRP Rs. 120 Net Wt. 500 g",
    "text_blocks": [
        {
            "text": "MRP Rs. 120",
            "confidence": 0.94,
            "box": [
                [20, 40],
                [200, 40],
                [200, 80],
                [20, 80]
            ]
        }
    ],
    "processed_image_path":
        "processed_images/catch_label_processed.jpg",
    "annotated_image_path":
        "annotated_images/catch_label_processed_annotated.jpg"
}
```

The result contains normal Python `int`, `float`, `bool`, `str` and
`list` values, so it can be serialized as JSON.

## Multiple-Image Processing

Same product ki front, back and side images can be processed together:

```python
from image_processor import process_product_images

result = process_product_images([
    "input_images/product_front.jpg",
    "input_images/product_back.jpg",
    "input_images/product_side.jpg"
])
```

Run multiple images from the terminal:

```powershell
python .\image_processor.py `
    ".\input_images\product_front.jpg" `
    ".\input_images\product_back.jpg"
```

Command Prompt version:

```bat
python image_processor.py "input_images\product_front.jpg" "input_images\product_back.jpg"
```

Multiple-image output includes:

- Total image count
- Successful image count
- Failed image count
- Combined extracted text
- Individual result for every image

## Individual Module Testing

Quality checker:

```powershell
python .\quality_checker.py ".\input_images\catch_label.jpg"
```

Preprocessing:

```powershell
python .\preprocess.py ".\input_images\catch_label.jpg"
```

OCR and annotation:

```powershell
python .\ocr.py ".\processed_images\catch_label_processed.jpg"
```

Complete integration:

```powershell
python .\image_processor.py ".\input_images\catch_label.jpg"
```

## Automated Tests

Run tests from the `ml_service` folder:

```powershell
python -m pytest .\tests\test_ocr.py -v
```

The tests cover:

- Missing image
- Unsupported image format
- Corrupt image
- No text detected
- JSON serialization
- Required output keys
- Multiple-image support

## Image-Quality Measurements

### Blur score

Blur is estimated using the variance of the Laplacian.

Starting thresholds:

- Below `25`: potentially unreadable
- `25–99`: blurry or poor
- `100` and above: acceptable sharpness

### Brightness

Brightness is the average grayscale pixel value from `0` to `255`.

Starting thresholds:

- Below `25`: extremely dark
- `25–59`: dark
- `60–200`: initially acceptable
- `201–240`: too bright
- Above `240`: extremely bright

These are initial engineering thresholds and may require tuning using
more real product-label images.

## Error Handling

The module safely handles:

- `IMAGE_NOT_FOUND`
- `INVALID_IMAGE_PATH`
- `UNSUPPORTED_FORMAT`
- `CORRUPT_IMAGE`
- `QUALITY_CHECK_FAILED`
- `PREPROCESSING_FAILED`
- `OUTPUT_FOLDER_CREATION_FAILED`
- `OCR_EXECUTION_FAILED`
- `ANNOTATED_IMAGE_SAVE_FAILED`
- No text detected

Error results may contain development fields such as:

```python
{
    "success": False,
    "error": "IMAGE_NOT_FOUND",
    "message": "Image not found",
    "quality": None,
    "full_text": "",
    "text_blocks": [],
    "processed_image_path": None,
    "annotated_image_path": None
}
```

The successful integration result preserves the required output format.

## Known Limitations

OCR accuracy is not perfect.

Results may be affected by:

- Blurry or low-resolution images
- Small printed text
- Curved product containers
- Reflections and glare
- Decorative fonts
- Mixed Hindi and English text
- Folded or partially hidden labels
- Complex image backgrounds
- Incorrect camera angle

Confidence scores are model estimates and do not guarantee that
detected text is correct.

The module identifies text and image quality only. It does not determine
whether a product legally complies with any specific rule.