# Use official Python 3.10 slim image as base
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Hugging Face Spaces (Docker SDK) expects the application to listen on port 7860 by default.
# The PORT environment variable allows overriding the port if needed.
ENV PORT=7860

# Install system dependencies required by OpenCV (cv2) and EasyOCR / PyTorch
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy requirements and install Python packages first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download EasyOCR model weights during build so they are baked into the image
RUN python -c "import easyocr; easyocr.Reader(['en', 'hi'], gpu=False)"

# Copy application source code
COPY . .

# Expose port 7860 (Hugging Face Spaces default port)
EXPOSE 7860

# Start FastAPI application with Uvicorn, binding to 0.0.0.0 and configurable $PORT
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-7860}"]
