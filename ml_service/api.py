import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

import easyocr
from fastapi import FastAPI, File, HTTPException, UploadFile
import uvicorn

import image_processor
import ocr
from field_extractor import extract_fields

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

_reader_singleton = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler:
    Loads EasyOCR.Reader as a singleton at service startup.
    This avoids repeated model-loading overhead on every request.
    """
    global _reader_singleton
    print("Loading EasyOCR.Reader singleton at startup...", flush=True)
    _reader_singleton = easyocr.Reader(["en", "hi"], gpu=False, verbose=False)

    # Patch easyocr.Reader in easyocr and ocr modules to return the singleton
    easyocr.Reader = lambda *args, **kwargs: _reader_singleton
    ocr.easyocr.Reader = lambda *args, **kwargs: _reader_singleton

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
