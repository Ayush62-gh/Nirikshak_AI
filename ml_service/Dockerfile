# Use official Python 3.10 slim image as base
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Hugging Face Spaces (Docker SDK) expects the application to listen on port 7860 by default.
# The PORT environment variable allows overriding the port if needed.
ENV PORT=7860

# System dependencies required by OpenCV (cv2) and PaddlePaddle CPU inference
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy requirements and install Python packages first to leverage Docker layer caching
# NOTE: torch is included because paddleocr==2.10.0 imports albumentations, which
# unconditionally does `from .pytorch import *` → `import torch` in its __init__.
# torchvision and easyocr are NOT included.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download PaddleOCR PP-OCRv3 English det + rec model weights during build
# so they are baked into the image and do not download at container startup.
RUN python -c "\
from paddleocr import PaddleOCR; \
PaddleOCR(lang='en', use_gpu=False, use_angle_cls=False, \
          enable_mkldnn=False, show_log=False, ocr_version='PP-OCRv3')"

# Copy application source code
COPY . .

# Expose port 7860 (Hugging Face Spaces default port)
EXPOSE 7860

# Start FastAPI application with Uvicorn, binding to 0.0.0.0 and configurable $PORT
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-7860}"]
