# Nirikshak AI — Backend API Contract

> **Authoritative Specification:** This document serves as the formal API contract for Team Members 2 (Frontend), 3 (ML Service / OCR), 4 (Rule Engine), and 5. The live Swagger interactive UI at `http://localhost:8000/docs` always reflects the current running implementation.

---

## Service Endpoints Overview

| Method | Endpoint | Description | Auth / Content-Type |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Health check endpoint | None |
| `POST` | `/api/scan` | Upload label image & trigger compliance scan | `multipart/form-data` (`image`) |
| `GET` | `/api/scans` | List historical scans (paginated) | None |
| `GET` | `/api/scans/{scan_id}` | Retrieve single scan details by ID | None |

---

## Detailed Endpoint Specifications

### 1. `GET /api/health`
Confirms the backend process is alive.

#### Response (`200 OK`)
```json
{
  "status": "ok"
}
```

---

### 2. `POST /api/scan`
Uploads a package label image (`.jpeg`, `.jpg`, `.png`), extracts text via OCR, validates compliance against Legal Metrology rules, and returns full scan analysis.

#### Request
- **Header:** `Content-Type: multipart/form-data`
- **Body Field:** `image` (binary file upload, max size 10MB)

#### Response (`201 Created`)
```json
{
  "scan_id": "c9a4b2a8-1234-4567-89ab-cdef01234567",
  "timestamp": "2026-08-23T15:00:00+00:00",
  "product": {
    "product_name": "Sample Biscuits 200g",
    "manufacturer": "ABC Foods Pvt Ltd",
    "net_quantity": "200 g",
    "mrp": "Rs. 45",
    "batch_number": "B12345",
    "mfg_date": "01/2026",
    "consumer_care": "1800-XXX-XXXX"
  },
  "extracted_fields": {
    "product_name": "Sample Biscuits 200g",
    "manufacturer": "ABC Foods Pvt Ltd",
    "net_quantity": "200 g",
    "mrp": "Rs. 45",
    "batch_number": "B12345",
    "mfg_date": "01/2026",
    "consumer_care": "1800-XXX-XXXX",
    "raw_ocr_text": "Sample Biscuits 200g ABC Foods Pvt Ltd Net Wt 200 g MRP Rs. 45 B12345 01/2026 Consumer Care: 1800-XXX-XXXX"
  },
  "compliance": {
    "status": "PARTIAL",
    "violations": [
      {
        "rule": "Rule 6",
        "description": "Consumer care details format unclear",
        "field": "consumer_care"
      }
    ]
  },
  "image_ref": "uploads/sample_label.jpg"
}
```

---

### 3. `GET /api/scans`
Retrieves paginated scan history.

#### Query Parameters
- `page` (optional integer, default `1`, min `1`)
- `limit` (optional integer, default `20`, min `1`, max `100`)

#### Response (`200 OK`)
```json
{
  "scans": [
    {
      "scan_id": "c9a4b2a8-1234-4567-89ab-cdef01234567",
      "timestamp": "2026-08-23T15:00:00+00:00",
      "product": {
        "product_name": "Sample Biscuits 200g",
        "manufacturer": "ABC Foods Pvt Ltd",
        "net_quantity": "200 g",
        "mrp": "Rs. 45",
        "batch_number": "B12345",
        "mfg_date": "01/2026",
        "consumer_care": "1800-XXX-XXXX"
      },
      "extracted_fields": {
        "product_name": "Sample Biscuits 200g"
      },
      "compliance": {
        "status": "PARTIAL",
        "violations": [
          {
            "rule": "Rule 6",
            "description": "Consumer care details format unclear",
            "field": "consumer_care"
          }
        ]
      },
      "image_ref": "uploads/sample_label.jpg"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 1
}
```

---

### 4. `GET /api/scans/{scan_id}`
Retrieves full details of a specific scan record by UUID.

#### Path Parameter
- `scan_id` (string, required UUID)

#### Response (`200 OK`)
*(Same schema as `POST /api/scan` response above)*

---

## Centralized Error Response Shapes

All client and server errors adhere to a standardized `ErrorResponse` JSON structure:

```json
{
  "error": "<error_code_identifier>",
  "detail": "<human_readable_explanation>"
}
```

### Error Scenarios & Status Codes

#### `400 Bad Request` (Invalid file format or file size exceeded)
```json
{
  "error": "invalid_image",
  "detail": "Invalid image content-type. Only image/jpeg and image/png are supported."
}
```

#### `404 Not Found` (Resource does not exist)
```json
{
  "error": "Not Found",
  "detail": "Scan with ID 'invalid-uuid-9999' not found"
}
```

#### `422 Unprocessable Entity` (Request validation failure)
```json
{
  "error": "validation_error",
  "detail": "Invalid request parameters or payload"
}
```

#### `502 Bad Gateway` (External OCR or Rule Engine call failed)
```json
{
  "error": "external_service_error",
  "detail": "OCR service connection timed out"
}
```

#### `500 Internal Server Error` (Unhandled backend server error)
```json
{
  "error": "internal_server_error",
  "detail": "Internal server error"
}
```
*Note: Raw stack traces are never exposed in 500 responses.*
