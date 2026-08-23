# Nirikshak AI - Legal Metrology Compliance Checking System (Backend)

> **Statutory Compliance Verification Backend for Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011**

---

## 🏛️ Architectural Principle

**The AI/OCR model is NOT responsible for deciding legal compliance.**

The system strictly adheres to the mandated pipeline:
```
Image Upload
    ↓
Image Preprocessing (Orientation, Contrast CLAHE, Bilateral Denoising)
    ↓
OCR / Computer Vision (Tesseract / Pluggable Cloud Providers)
    ↓
Declaration Extraction (NLP & Regex normalization)
    ↓
Normalized Product Data
    ↓
Rule-Based Compliance Engine (Official Legal Metrology Rules, 2011)
    ↓
Violations with Evidence
    ↓
Weighted Compliance Score
    ↓
PDF Compliance Audit Report Generation (ReportLab)
    ↓
PostgreSQL Database + Dashboard Analytics API
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.12+ (tested on Python 3.13)
- Tesseract OCR (optional for mock testing, required for live OCR)
- PostgreSQL (or local SQLite fallback)

### 2. Setup Virtual Environment & Install Dependencies
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file (copied from `.env.example`):
```bash
cp .env.example .env
```

Default configuration in `.env`:
```ini
APP_NAME="Nirikshak AI - Legal Metrology Compliance Engine"
APP_ENV=development
DEBUG=True
API_V1_STR=/api/v1
DATABASE_URL=sqlite+aiosqlite:///./nirikshak.db
JWT_SECRET=supersecretjwtkeyfornirikshaklegalmetrologycompliancesystem2026
ACCESS_TOKEN_EXPIRE_MINUTES=1440
UPLOAD_DIR=uploads
REPORT_DIR=reports
MAX_UPLOAD_SIZE_MB=25
OCR_PROVIDER=tesseract
```

### 4. Run Migrations & Start Server
```bash
# Run Alembic migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

* **Interactive OpenAPI Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🐳 Docker Deployment

To launch the full backend and PostgreSQL database using Docker Compose:
```bash
docker-compose up --build -d
```

---

## 🧪 Running Automated Tests

Run the complete 25-test suite:
```bash
pytest tests/ -v
```

---

## 📜 Legal Metrology (Packaged Commodities) Rules, 2011 Mapping

| Rule ID | Statutory Reference | Requirement | Category | Severity | Weight |
|---|---|---|---|---|---|
| **LM-PC-001** | Rule 6(1)(e) | Retail Sale Price (MRP) with mandatory *'inclusive of all taxes'* statement | `MRP` | `CRITICAL` | 20 |
| **LM-PC-002** | Rule 6(1)(c) / Rule 13 | Net Quantity declaration in standard SI units (`g`, `kg`, `ml`, `l`, `N`, `U`) | `QUANTITY` | `CRITICAL` | 20 |
| **LM-PC-003** | Rule 6(1)(d) | Month and Year of Manufacture / Pre-packing (`MM/YYYY` format) | `DATE` | `HIGH` | 15 |
| **LM-PC-004** | Rule 6(1)(a) | Manufacturer / Packer name and complete address with 6-digit PIN code | `MANUFACTURER` | `HIGH` | 15 |
| **LM-PC-005** | Rule 6(1)(g) | Consumer Care Email address for complaints | `CONSUMER_CARE` | `HIGH` | 10 |
| **LM-PC-006** | Rule 6(1)(g) | Consumer Care Telephone / Toll-free helpline number | `CONSUMER_CARE` | `HIGH` | 10 |
| **LM-PC-007** | Rule 6(1)(b) | Generic Commodity / Product Name | `DECLARATION` | `MEDIUM` | 5 |
| **LM-PC-008** | Rule 6(1)(f) | Country of Origin for imported packaged commodities | `IMPORTER` | `HIGH` | 5 |

---

## 🌐 Complete API Endpoint Reference

### 1. Authentication
* `POST /api/v1/auth/register` - Register a new inspector / admin / viewer
* `POST /api/v1/auth/login` - Authenticate and obtain JWT Bearer access token
* `GET /api/v1/auth/me` - Get profile of currently authenticated user

### 2. Products
* `POST /api/v1/products` - Create new packaged commodity catalog item
* `GET /api/v1/products` - List products with text search and pagination
* `GET /api/v1/products/{id}` - Get product details by ID
* `PUT /api/v1/products/{id}` - Update product details
* `DELETE /api/v1/products/{id}` - Delete product (Admin only)

### 3. Inspections & Scans
* `POST /api/v1/inspections` - Create new inspection session
* `POST /api/v1/inspections/{id}/images` - Upload packaged label images (JPEG, PNG, WEBP)
* `POST /api/v1/inspections/{id}/scan` - Execute full scanning, OCR, and compliance engine pipeline
* `GET /api/v1/inspections/{id}` - Get complete inspection details with extracted declarations and violations
* `GET /api/v1/inspections` - Paginated inspection list with status/result filtering
* `GET /api/v1/inspections/{id}/violations` - Retrieve detected violations

### 4. PDF Compliance Reports
* `GET /api/v1/reports/{inspection_id}` - Download / stream generated PDF compliance audit report
* `POST /api/v1/reports/{inspection_id}/generate` - Trigger PDF report generation

### 5. Dashboard & Analytics
* `GET /api/v1/dashboard/summary` - Aggregate metrics (total inspections, compliance rate, violation counts by severity)
* `GET /api/v1/dashboard/trends` - Top violation types and category compliance trends

### 6. System Health
* `GET /health` - Live database and service health check
