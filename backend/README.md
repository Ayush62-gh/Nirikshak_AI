# Nirikshak AI - Backend Service

Backend service for Nirikshak AI (Legal Metrology Packaged Commodities compliance checker), built with Python, FastAPI, and SQLAlchemy.

---

## Quick Start & Setup Instructions

### 1. Clone & Navigate
```bash
git clone https://github.com/Ayush62-gh/Nirikshak_AI.git
cd Nirikshak_AI/backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv
```

### 3. Activate Virtual Environment
- **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (CMD):**
  ```cmd
  venv\Scripts\activate.bat
  ```
- **Linux / macOS:**
  ```bash
  source venv/bin/activate
  ```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

#### Environment Variable Descriptions:
| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `OCR_SERVICE_URL` | `http://localhost:5001` | URL for the ML/OCR service (Member 3) |
| `RULE_ENGINE_URL` | `http://localhost:5002` | URL for the Rule Engine service (Member 4) |
| `PORT` | `8000` | Local port for the FastAPI server |
| `DATABASE_URL` | `sqlite:///./app/db/nirikshak.db` | SQLAlchemy SQLite database connection string |
| `USE_MOCK_OCR` | `True` | Set to `True` to use mocked OCR response; `False` for live HTTP call |
| `USE_MOCK_RULE_ENGINE` | `True` | Set to `True` to use mocked Rule Engine response; `False` for live HTTP call |

> **Note on Mock Mode:** `USE_MOCK_OCR` and `USE_MOCK_RULE_ENGINE` are enabled (`True`) by default so that the backend can be developed and tested independently before Members 3 & 4 deploy their live microservices.

---

## Running the Backend Server

Start the development server with live reload:
```bash
uvicorn app.main:app --reload --port 8000
```

### Server Verification
- **Health Check Endpoint:** [http://localhost:8000/api/health](http://localhost:8000/api/health)
- **Interactive Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Open API Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Example API Usage (`POST /api/scan`)

### Using `curl`:
```bash
curl -X 'POST' \
  'http://localhost:8000/api/scan' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'image=@sample_label.jpg;type=image/jpeg'
```

### Using Interactive Docs:
1. Open [http://localhost:8000/docs](http://localhost:8000/docs).
2. Expand `POST /api/scan`.
3. Click **Try it out**, select an image file (`.jpg` or `.png`), and click **Execute**.

---

## Running Automated Tests

Run the complete pytest test suite:
```bash
pytest -v
```
