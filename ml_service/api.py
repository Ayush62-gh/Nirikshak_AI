import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
import uvicorn

import image_processor
import paddle_ocr
from field_extractor import extract_fields

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler:
    Loads the configured OCR reader singleton (PaddleOCR by default, or EasyOCR
    if OCR_ENGINE=easyocr) at service startup to avoid repeated model-loading overhead.
    """
    engine = os.getenv("OCR_ENGINE", "paddle").strip().lower()
    if engine in ("easyocr", "easy_ocr", "easy"):
        import easyocr
        import ocr
        print("Loading EasyOCR.Reader singleton at startup...", flush=True)
        _reader = easyocr.Reader(["en", "hi"], gpu=False, verbose=False)
        easyocr.Reader = lambda *args, **kwargs: _reader
        ocr.easyocr.Reader = lambda *args, **kwargs: _reader
    else:
        print("Loading PaddleOCR PP-OCRv3 reader singleton at startup...", flush=True)
        paddle_ocr.get_paddle_reader()
    yield


app = FastAPI(
    title="Nirikshak AI - ML Service API",
    description="HTTP wrapper around OCR image processing pipeline",
    lifespan=lifespan
)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/extract")
def extract_text_from_image(file: UploadFile = File(...)):
    """
    Processes an uploaded product image and returns extracted text and quality info.
    
    Accepts: multipart/form-data with field named 'file'
    """
    filename = file.filename or ""
    file_ext = Path(filename).suffix.lower()

    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid image format: '{file_ext}'. "
                f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )
        )

    contents = file.file.read()
    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    # Temporary file creation
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
    try:
        temp_file.write(contents)
        temp_file.close()

        result = image_processor.process_product_image(temp_file.name)

        if isinstance(result, dict) and result.get("success") is False:
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "Image processing failed.")
            )

        result["fields"] = extract_fields(result)

        return result

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Image processing failed: {str(error)}"
        )

    finally:
        if os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except OSError:
                pass


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)
