# Hugging Face Spaces Deployment Guide — ML Service

This guide explains how to deploy the **Nirikshak AI ML Service** as a Docker-SDK Space on **Hugging Face Spaces**.

---

## 1. Space Configuration (`README.md` Front-Matter)

Hugging Face Docker Spaces require a YAML metadata header at the very top of `README.md` in the Space repository.

When initializing your Hugging Face Space repository, ensure the top of `README.md` contains the following metadata:

```yaml
---
title: Nirikshak AI - ML Service
emoji: 🔍
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---
```

### Key Fields:
- `sdk: docker`: Directs Hugging Face to build and run the image defined in `Dockerfile`.
- `app_port: 7860`: Configures HF Spaces routing to proxy traffic to container port `7860`.

---

## 2. Step-by-Step Manual Deployment Options

### Prerequisites
1. Create a free account at [huggingface.co](https://huggingface.co).
2. Create a new Space:
   - Navigate to **Hugging Face > New Space**.
   - Choose a Space name (e.g., `nirikshak-ml-service`).
   - Select **Docker** as the Space SDK.
   - Choose **Blank** (or custom) template.
   - Choose **Public** or **Private** visibility.

---

### Option A: Deploy via Git (Recommended)

1. Clone your newly created Hugging Face Space repository:
   ```bash
   git clone https://huggingface.co/spaces/<YOUR-USERNAME>/<YOUR-SPACE-NAME>
   cd <YOUR-SPACE-NAME>
   ```

2. Copy all contents of the `ml_service/` directory into the cloned Space directory:
   - `Dockerfile`
   - `.dockerignore`
   - `requirements.txt`
   - `api.py`
   - `ocr.py`
   - `preprocess.py`
   - `quality_checker.py`
   - `field_extractor.py`
   - `image_processor.py`
   - `README.md` (with the required YAML front-matter at the top)

3. Commit and push to Hugging Face:
   ```bash
   git add .
   git commit -m "Deploy ML service to Hugging Face Spaces"
   git push origin main
   ```

HF Spaces will automatically detect the `Dockerfile`, build the container, and launch the FastAPI server.

---

### Option B: Deploy via Hugging Face CLI (`huggingface_hub`)

1. Install the Hugging Face CLI:
   ```bash
   pip install huggingface_hub
   ```

2. Log in with your Hugging Face Access Token (User Access Token with Write permissions):
   ```bash
   huggingface-cli login
   ```

3. Upload the `ml_service` directory directly to your Space:
   ```bash
   huggingface-cli upload <YOUR-USERNAME>/<YOUR-SPACE-NAME> ./ml_service . --repo-type=space
   ```

---

## 3. Environment Variables & Secrets Management

- **Do NOT commit `.env` files or API secrets** to the repository.
- To set custom environment variables or sensitive keys:
  1. Go to your Space on Hugging Face.
  2. Navigate to **Settings** > **Variables and secrets**.
  3. Click **New secret** or **New variable** (e.g. `PORT` if overriding defaults, or custom authentication tokens).
- Hugging Face automatically injects these as environment variables into the running Docker container at runtime.

---

## 4. Service Health & API Endpoints

Once deployed, the space URL will serve the FastAPI application:
- Health Check: `GET https://<YOUR-SPACE-NAME>.hf.space/health`
- OCR Extraction: `POST https://<YOUR-SPACE-NAME>.hf.space/extract`
