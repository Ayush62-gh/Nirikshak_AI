# Legal Metrology Compliance Rule Engine

A standalone, modular Rule Engine microservice built for **Nirikshak AI** under **SIH (Smart India Hackathon) Problem Statement 26034**. 

This microservice evaluates structured product declaration payloads against statutory compliance rules defined under the **Legal Metrology (Packaged Commodities) Rules, 2011** (and applicable amendments), returning deterministic compliance decisions (`PASS`, `FAIL`, `MANUAL_REVIEW`, `NOT_APPLICABLE`).

Default running port: **`5002`**

---

## 📁 1. Project Folder Structure

```
rule_engine/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI Application Entrypoint (port 5002)
│   ├── api/                        # REST API Layer
│   │   ├── __init__.py
│   │   ├── routes.py               # API Endpoints (/health, /api/v1/compliance/check)
│   │   └── dependencies.py         # Route Dependency Injection
│   ├── core/                       # Engine Architecture & Pipelines
│   │   ├── __init__.py
│   │   ├── interface.py            # AbstractRule ABC Interface
│   │   ├── selector.py             # Rule Selector Component
│   │   ├── executor.py             # Rule Executor Component
│   │   └── engine.py               # Rule Engine Coordinator
│   ├── rules/                      # Active Statutory Rule Implementations
│   │   ├── __init__.py             # Rule Registry Exports
│   │   ├── base.py                 # Rule Registry & Base Helpers
│   │   ├── mrp_rule.py             # Rule 6(1)(e): Maximum Retail Price Rule
│   │   ├── net_quantity_rule.py    # Rule 6(1)(c): Net Quantity Rule
│   │   ├── importer_rule.py        # Rule 6(1)(a): Importer Name & Address Rule
│   │   ├── product_name_rule.py    # Rule 6(1)(b): Generic Commodity Name Rule
│   │   ├── mfg_name_rule.py        # Rule 6(1)(a): Manufacturer/Packer Name Rule
│   │   ├── mfg_address_rule.py     # Rule 6(1)(a): Manufacturer/Packer Address Rule
│   │   ├── date_of_packing_rule.py # Rule 6(1)(e): Month & Year of Packing Rule
│   │   ├── consumer_care_rule.py   # Rule 6(1)(h): Consumer Care Details Rule
│   │   ├── country_of_origin_rule.py # Rule 6(1)(ab): Country of Origin Rule
│   │   ├── unit_sale_price_rule.py # Rule 6(11): Unit Sale Price (USP) Rule
│   │   ├── expiry_date_rule.py     # Rule 6(1)(d): Best Before / Expiry Date Rule
│   │   └── font_height_rule.py     # Rule 7 & 9: Font Height & Readability Rule
│   ├── models/                     # Pydantic Schemas & DTOs
│   │   ├── __init__.py
│   │   ├── product.py              # EvaluateProductRequest & ProductData
│   │   ├── rule_result.py          # IndividualRuleResult, RuleStatus, RuleSeverity
│   │   ├── compliance.py           # EvaluateComplianceResponse & ComplianceReport
│   │   └── evidence.py             # FieldEvidence & Provenance Metadata
│   ├── generator/                  # Result Aggregation
│   │   ├── __init__.py
│   │   └── summary_generator.py    # Compliance Aggregator
│   └── exceptions/                 # Exception Handlers
│       ├── __init__.py
│       ├── custom_exceptions.py    # Custom Domain Exceptions
│       └── handlers.py             # FastAPI Exception Handlers
├── tests/                          # Automated Pytest Suite (64 tests)
│   ├── test_api_v1.py              # API v1 Integration Tests
│   ├── test_care_rule.py           # Consumer Care Rule Unit Tests
│   ├── test_coo_rule.py            # Country of Origin Rule Unit Tests
│   ├── test_date_rule.py           # Packing Date Rule Unit Tests
│   ├── test_engine.py              # Core Engine Orchestrator Tests
│   ├── test_evidence_provenance.py # Evidence Provenance Tests
│   ├── test_expiry_rule.py         # Expiry Date Rule Unit Tests
│   ├── test_font_rule.py           # Font Height Rule Unit Tests
│   ├── test_health.py              # Health Check Endpoint Test
│   ├── test_importer_rule.py       # Importer Rule Unit Tests
│   ├── test_manufacturer_rules.py  # Manufacturer Name & Address Unit Tests
│   ├── test_mrp_rule.py            # MRP Rule Unit Tests
│   ├── test_net_quantity_rule.py   # Net Quantity Rule Unit Tests
│   └── test_usp_rule.py            # Unit Sale Price Rule Unit Tests
├── .env.example                    # Environment Template
├── .gitignore                      # Git Ignore File
├── RULE_MATRIX.md                  # Comprehensive Statutory Legal Matrix
├── README.md                       # Microservice Documentation
└── requirements.txt                # Python Dependencies
```

---

## 📜 2. Statutory Rules Summary Table

The Rule Engine implements 14 active statutory compliance rules. For complete legal descriptions, PASS/FAIL criteria, and statutory references, consult [`RULE_MATRIX.md`](file:///c:/Users/sonim/New%20folder/Nirikshak_AI/rule_engine/RULE_MATRIX.md).

| Rule ID | Rule Name | Target Field | Severity |
| :--- | :--- | :--- | :--- |
| `LM-RULE-MRP-001` | Maximum Retail Price (MRP) Declaration Check | `mrp` | `CRITICAL` |
| `LM-RULE-NETQTY-002` | Net Quantity Declaration Check | `netQuantity` | `HIGH` |
| `LM-RULE-IMP-003` | Importer Name & Address Check for Foreign Commodities | `importerName` | `CRITICAL` |
| `LM-RULE-NAME-004` | Generic / Commodity Name Declaration Check | `productName` | `HIGH` |
| `LM-RULE-MFGNAME-005` | Manufacturer or Packer Name Declaration Check | `manufacturerName` | `CRITICAL` |
| `LM-RULE-MFGADDR-006` | Manufacturer or Packer Address Declaration Check | `manufacturerAddress` | `HIGH` |
| `LM-RULE-DATE-007` | Month and Year of Packing / Manufacture Check | `monthOfPacking` | `HIGH` |
| `LM-RULE-CARE-008` | Consumer Care Details Declaration Check | `consumerCare` | `HIGH` |
| `LM-RULE-COO-009` | Country of Origin Declaration Check | `countryOfOrigin` | `CRITICAL` |
| `LM-RULE-USP-010` | Unit Sale Price (USP) Declaration Check | `unitSalePrice` | `HIGH` |
| `LM-RULE-EXP-011` | Best Before / Expiry Date Declaration Check | `expiryDate` | `HIGH` |
| `LM-RULE-FONT-012` | Font Size & Readability Analysis Check | `fontSizeMm` | `HIGH` |
| `LM-RULE-PLACE-013` | Declaration Placement & PDP Panel Check | `declarationPlacement` | `HIGH` |
| `LM-RULE-READ-014` | Physical Legibility & Color Contrast Check | `contrastRatio` | `HIGH` |

---

## 🔌 3. API Endpoints

### Canonical Endpoint (Production)
- **`POST /api/v1/compliance/check`**: Canonical endpoint for evaluating structured product payloads. Used directly by the backend orchestrator (`backend/app/services/rule_client.py`).

### Legacy & Deprecated Endpoints (Backward Compatibility)
- **`POST /api/rules/evaluate`** *(Deprecated)*: Teammate API contract legacy alias. Delegates to the core engine and returns `EvaluateComplianceResponse`.
- **`POST /api/v1/compliance/evaluate`** *(Deprecated)*: Internal legacy endpoint accepting `ProductData` schema and returning `ComplianceReport`.

### Health Check Endpoints
- **`GET /health`** or **`GET /api/v1/health`**: Returns HTTP 200 health status JSON (`{"status": "healthy", "service": "...", "version": "1.0.0"}`).

### Sample Request Payload (`POST /api/v1/compliance/check`)
```json
{
  "productId": "PROD-12345",
  "productName": "Organic Herbal Green Tea",
  "productType": "food",
  "isImported": false,
  "manufacturerName": "Himalayan Tea Packers Pvt Ltd",
  "manufacturerAddress": "Industrial Area, Sector 5, Haridwar - 249401",
  "netQuantity": "250 g",
  "mrp": "Rs. 250.00 (incl. of all taxes)",
  "unitSalePrice": "Rs 1.00/g",
  "monthOfPacking": "08",
  "yearOfPacking": "2026",
  "expiryDate": "Best Before 12 Months from packing",
  "consumerCare": "care@himalayantea.com, Ph: 1800-123-4567"
}
```

### Sample Response Payload (`EvaluateComplianceResponse`)
```json
{
  "productId": "PROD-12345",
  "overallStatus": "PASS",
  "totalRulesEvaluated": 12,
  "passedRules": 12,
  "failedRules": 0,
  "manualReviewRules": 0,
  "notApplicableRules": 0,
  "individualRuleResults": [
    {
      "ruleId": "LM-RULE-MRP-001",
      "ruleName": "Maximum Retail Price (MRP) Declaration Check",
      "status": "PASS",
      "severity": "CRITICAL",
      "message": "Statutory MRP declaration is valid with required numeric price and tax clause.",
      "field": "mrp",
      "evidence": null
    },
    {
      "ruleId": "LM-RULE-NETQTY-002",
      "ruleName": "Net Quantity Declaration Check",
      "status": "PASS",
      "severity": "HIGH",
      "message": "Net Quantity declaration is valid: '250 g'.",
      "field": "netQuantity",
      "evidence": null
    },
    {
      "ruleId": "LM-RULE-MFGADDR-006",
      "ruleName": "Manufacturer or Packer Address Declaration Check",
      "status": "PASS",
      "severity": "HIGH",
      "message": "Manufacturer or Packer address text is present with 6-digit pincode.",
      "field": "manufacturerAddress",
      "evidence": null
    }
  ]
}
```

---

## 📊 4. Deterministic Status Aggregation

The engine aggregates overall product compliance using a strict status precedence hierarchy:

`FAIL > MANUAL_REVIEW > PASS > NOT_APPLICABLE`

- **`FAIL`**: Triggered if **at least 1** applicable rule returns `FAIL`.
- **`MANUAL_REVIEW`**: Triggered if **0** rules fail, but **at least 1** applicable rule returns `MANUAL_REVIEW`.
- **`PASS`**: Triggered if **0** rules fail or require manual review, and **at least 1** applicable rule returns `PASS`.
- **`NOT_APPLICABLE`**: Returned when a rule is excluded due to product metadata (e.g. Importer rule on domestic products).

---

## 🏃 5. How to Run and Test

### Environment Setup & Installation
```bash
cd rule_engine
pip install -r requirements.txt
```

### Configuration
The microservice is configured using environment variables defined in `.env.example`:
- `HOST`: Server host network binding
- `PORT`: Service port (default: `5002`)
- `ENVIRONMENT`: Application runtime environment mode
- `LOG_LEVEL`: Logging verbosity level

Copy `.env.example` to `.env` to customize settings:
```bash
cp .env.example .env
```

### Running the API Server
Start the Uvicorn server on port **`5002`**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 5002
```
Access interactive API docs at: `http://localhost:5002/docs`

### Running the Test Suite
Execute pytest across all rule tests:
```bash
python -m pytest -q
```

---

## ⚠️ 6. Known Limitations

1. **Official Legal Text Verification**: Legal references and statutory thresholds are pending final official verification against government gazette notifications.
2. **Font Height Thresholds**: `FontHeightRule` currently validates basic physical font measurements (>= 1.0 mm) and lacks dynamic threshold tables mapped to package principal display area.
3. **Unit Sale Price (USP) Thresholds**: Missing USP on packages with `netQuantity` defaults conservatively to `MANUAL_REVIEW` pending verification of Rule 6(11) statutory package size thresholds.
4. **Postal Pincode Regex Heuristics**: 6-digit numbers in address text (such as licence or batch numbers) can be matched by regex as Indian postal pincodes.
5. **MRP Currency Symbol Tolerance**: MRP rule allows `PASS` if numeric price digits and statutory tax inclusion clauses (`incl. of all taxes`) are present, without strictly requiring a currency symbol (`₹` or `Rs`).
6. **Visual & PDP PDP Layout Constraints**: Principal Display Panel placement, legibility, and contrast checks depend on visual metrics from `ml_service` and are not evaluated solely by structured JSON payload text rules.
