import os
import re
import uuid
from pathlib import Path
from typing import Set, Tuple
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.core.logging import logger

ALLOWED_IMAGE_MIMES: Set[str] = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/tiff",
}

ALLOWED_EXTENSIONS: Set[str] = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".tiff",
    ".tif",
}


def sanitize_filename(filename: str) -> str:
    """Sanitize and strip unsafe characters from filename."""
    # Keep only alphanumerics, dots, underscores, hyphens
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
    return clean


def validate_image_file(file: UploadFile) -> str:
    """
    Validate that an uploaded file is a valid image based on extension and content type.
    Returns the sanitized extension.
    """
    if not file.filename:
        raise ValidationError("Uploaded file must have a valid filename")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Invalid file extension '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Check content type if provided
    content_type = file.content_type.lower() if file.content_type else ""
    if content_type and content_type not in ALLOWED_IMAGE_MIMES:
        raise ValidationError(
            f"Invalid file MIME type '{content_type}'. Allowed types: {', '.join(sorted(ALLOWED_IMAGE_MIMES))}"
        )

    return ext


async def save_upload_image(file: UploadFile, subfolder: str = "") -> Tuple[str, int, str]:
    """
    Safely save an uploaded image with a unique filename.
    Returns: (relative_file_path, file_size_bytes, mime_type)
    """
    ext = validate_image_file(file)
    unique_filename = f"{uuid.uuid4().hex}{ext}"

    # Determine destination directory
    dest_dir = settings.upload_path
    if subfolder:
        dest_dir = dest_dir / sanitize_filename(subfolder)
        dest_dir.mkdir(parents=True, exist_ok=True)

    dest_path = dest_dir / unique_filename

    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    total_bytes = 0

    try:
        with open(dest_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # Read 1MB chunks
                total_bytes += len(chunk)
                if total_bytes > max_size_bytes:
                    # Clean up partial file
                    buffer.close()
                    if dest_path.exists():
                        dest_path.unlink()
                    raise ValidationError(
                        f"File size exceeds maximum permitted limit of {settings.MAX_UPLOAD_SIZE_MB}MB"
                    )
                buffer.write(chunk)
    except Exception as e:
        if dest_path.exists():
            dest_path.unlink()
        if isinstance(e, ValidationError):
            raise
        logger.error(f"Failed to write uploaded file {unique_filename}: {e}")
        raise ValidationError(f"Could not save uploaded file: {str(e)}")
    finally:
        await file.seek(0)

    # Calculate path relative to uploads directory
    relative_path = os.path.relpath(dest_path, settings.upload_path.parent)
    mime_type = file.content_type or f"image/{ext.lstrip('.')}"

    return str(relative_path).replace("\\", "/"), total_bytes, mime_type


def get_absolute_path(relative_path: str) -> Path:
    """Resolve a relative storage path into an absolute Path."""
    p = Path(relative_path)
    if p.is_absolute():
        return p
    return settings.upload_path.parent / p
