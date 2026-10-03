import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

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
    Loads the configured OCR reader singleton (PaddleOCR) at service startup to avoid repeated model-loading overhead.
    """
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


@app.post("/extract-multi")
def extract_text_from_multiple_images(files: List[UploadFile] = File(...)):
    """
    Processes multiple uploaded product images (e.g., front, back, side labels)
    and returns merged Metrology fields with consensus & conflict resolution.
    
    Accepts: multipart/form-data with repeated field named 'files'
    """
    if not files:
        raise HTTPException(
            status_code=400,
            detail="No files provided."
        )

    temp_paths = []
    try:
        for file in files:
            filename = file.filename or ""
            file_ext = Path(filename).suffix.lower()
            if file_ext not in SUPPORTED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Invalid image format in file '{filename}': '{file_ext}'. "
                        f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
                    )
                )

            contents = file.file.read()
            if not contents:
                raise HTTPException(
                    status_code=400,
                    detail=f"Uploaded file '{filename}' is empty."
                )

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
            temp_file.write(contents)
            temp_file.close()
            temp_paths.append(temp_file.name)

        result = image_processor.process_product_images(temp_paths)

        if isinstance(result, dict) and result.get("success") is False:
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "Multi-image processing failed.")
            )

        return result

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Multi-image processing failed: {str(error)}"
        )

    finally:
        for p in temp_paths:
            if os.path.exists(p):
                try:
                    os.unlink(p)
                except OSError:
                    pass


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)
