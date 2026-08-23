# Legal Metrology Compliance Rule Engine

A standalone, modular Rule Engine microservice designed according to the **Legal Metrology (Packaged Commodities) Rules, 2011**.

This backend service evaluates structured product declaration data, runs applicable statutory compliance rules, and generates structured compliance summary reports.

---

## 📁 1. Project Folder Structure

```
rule_engine/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI Application Entrypoint & Factory
│   ├── api/                        # API Layer
│   │   ├── __init__.py
│   │   ├── routes.py               # REST API Routes (/health, /evaluate)
│   │   └── dependencies.py         # Route Dependency Injections
│   ├── models/                     # Data Transfer Objects (DTOs)
│   │   ├── __init__.py
│   │   ├── product.py              # Input Product DTOs & Validation Schema
│   │   ├── rule_result.py          # Individual Rule Execution Result Schema
│   │   └── compliance.py           # Overall Compliance Summary Schema
│   ├── core/                       # Rule Engine Core Architecture
│   │   ├── __init__.py
│   │   ├── interface.py            # Abstract Rule Interface (AbstractRule ABC)
│   │   ├── selector.py             # Rule Selector component
│   │   ├── executor.py             # Rule Executor component
│   │   └── engine.py               # Rule Engine Coordinator
│   ├── rules/                      # Rule Classes (Statutory Rule Skeletons)
│   │   ├── __init__.py
│   │   ├── base.py                 # Rule Registry & Base Helpers
│   │   ├── mrp_rule.py             # Rule 6(1)(e): MRP Declaration Rule Skeleton
│   │   └── net_quantity_rule.py    # Rule 6(1)(c): Net Quantity Rule Skeleton
│   ├── generator/                  # Compliance Result Generator
│   │   ├── __init__.py
│   │   └── summary_generator.py    # Compliance Score & Summary Aggregator
│   └── exceptions/                 # Exception/Error Handling
│       ├── __init__.py
│       ├── custom_exceptions.py    # Custom Exception Classes
│       └── handlers.py             # FastAPI Exception Handlers
├── tests/                          # Test Suite
│   ├── __init__.py
│   ├── test_health.py              # Health check endpoint test
│   └── test_engine.py              # Rule Engine pipeline unit tests
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore patterns
├── README.md                       # Project Documentation
└── requirements.txt                # Python Dependencies
```

---

## ⚙️ 2. Component Responsibilities

| Component | Directory / File | Responsibility |
| :--- | :--- | :--- |
| **API Layer** | `app/api/routes.py` | Handles incoming HTTP endpoints (`GET /health`, `POST /api/v1/compliance/evaluate`), validates request payloads, and returns JSON responses. |
| **Model / DTOs** | `app/models/` | Defines strict Pydantic schemas (`ProductData`, `RuleResult`, `ComplianceReport`) for input validation and structured responses. |
| **Rule Interface** | `app/core/interface.py` | Defines `AbstractRule` ABC contract enforcing `rule_id`, `rule_name`, `category`, `is_applicable()`, and `evaluate()`. |
| **Rule Selector** | `app/core/selector.py` | Filters all registered rules to select only rules applicable to the given product metadata/category. |
| **Rule Executor** | `app/core/executor.py` | Safely executes selected rules sequentially or concurrently, catching rule-level exceptions without crashing the process. |
| **Rule Engine Core** | `app/core/engine.py` | Main orchestrator coordinating the execution pipeline: `ProductData` $\rightarrow$ `Selection` $\rightarrow$ `Execution` $\rightarrow$ `Summary`. |
| **Individual Rules** | `app/rules/` | Statutory rule implementations (e.g. MRP check, Net Quantity check) registered with `RuleRegistry`. |
| **Result Generator**| `app/generator/` | Aggregates individual rule results, computes the overall compliance score (0-100%), count metrics, and PASS/FAIL status. |
| **Exception Handling**| `app/exceptions/` | Custom domain exceptions (`ProductDataValidationError`, `RuleExecutionError`) converted into standard structured JSON responses. |

---

## 🔄 3. Execution Pipeline Flow

```
Structured Product Data (JSON)
          ↓
  [Input Validation]  (Pydantic Models)
          ↓
  [Rule Selection]    (RuleSelector)
          ↓
  [Rule Execution]    (RuleExecutor)
          ↓
[Individual Results]  (List[RuleResult])
          ↓
[Compliance Summary]  (ComplianceResultGenerator)
          ↓
   JSON Response      (ComplianceReport)
```

---

## 🚀 4. How to Run the Project

### Prerequisites
- Python 3.9+ installed

### Step 1: Navigate to `rule_engine` directory
```bash
cd rule_engine
```

### Step 2: Create and activate virtual environment (Optional but Recommended)
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the FastAPI dev server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 5002
```

### Step 5: Run tests
```bash
pytest
```

---

## 📡 5. Available API Endpoints

### 1. Teammates Integration Endpoint (API Contract)
- **URL**: `POST /api/rules/evaluate`
- **Content-Type**: `application/json`
- **Description**: Main contract endpoint for communicating between the Rule Engine and external/teammates' backend services. Supports structured product fields regardless of data source (OCR, AI, Manual Entry, E-Commerce).

#### Sample Request JSON (`EvaluateProductRequest`):
```json
{
  "productId": "PROD-88210",
  "productName": "Organic Herbal Green Tea",
  "productType": "food",
  "isImported": false,
  "manufacturerName": "Ayurveda Organics Pvt Ltd",
  "manufacturerAddress": "Plot 12, Industrial Estate, Haridwar",
  "packerName": null,
  "importerName": null,
  "netQuantity": "100 g",
  "mrp": "Rs. 299.00 (incl. of all taxes)",
  "monthOfPacking": "08",
  "yearOfPacking": "2026",
  "consumerCare": "Email: care@ayurvedaorganics.com, Tel: 1800-888-9999",
  "countryOfOrigin": "India"
}
```

#### Sample Response JSON (`EvaluateComplianceResponse`):
```json
{
  "productId": "PROD-88210",
  "overallStatus": "FAIL",
  "totalRules": 5,
  "passedRules": 3,
  "failedRules": 1,
  "manualReviewRules": 1,
  "individualRuleResults": [
    {
      "ruleId": "LM-RULE-MRP-001",
      "ruleName": "Maximum Retail Price (MRP) Declaration Check",
      "status": "PASS",
      "severity": "CRITICAL",
      "message": "MRP declaration is present with mandatory tax inclusion statement."
    },
    {
      "ruleId": "LM-RULE-NETQTY-002",
      "ruleName": "Net Quantity Declaration Check",
      "status": "PASS",
      "severity": "HIGH",
      "message": "Net Quantity declaration is present in standard metric units."
    },
    {
      "ruleId": "LM-RULE-MFG-003",
      "ruleName": "Manufacturer / Packer Address Declaration Check",
      "status": "FAIL",
      "severity": "HIGH",
      "message": "Manufacturer address is incomplete; missing pincode/city details."
    },
    {
      "ruleId": "LM-RULE-DATE-004",
      "ruleName": "Month and Year of Packing Check",
      "status": "MANUAL_REVIEW",
      "severity": "MEDIUM",
      "message": "Month/Year format requires verification against statutory date guidelines."
    },
    {
      "ruleId": "LM-RULE-IMP-005",
      "ruleName": "Importer Name & Address Check for Foreign Goods",
      "status": "NOT_APPLICABLE",
      "severity": "CRITICAL",
      "message": "Rule not applicable for non-imported commodities."
    }
  ],
  "violations": [
    {
      "ruleId": "LM-RULE-MFG-003",
      "ruleName": "Manufacturer / Packer Address Declaration Check",
      "severity": "HIGH",
      "message": "Manufacturer address is incomplete; missing pincode/city details.",
      "remediation": "Ensure complete street, city, state, and 6-digit pincode are provided."
    },
    {
      "ruleId": "LM-RULE-DATE-004",
      "ruleName": "Month and Year of Packing Check",
      "severity": "MEDIUM",
      "message": "Month/Year format requires verification against statutory date guidelines.",
      "remediation": "Confirm date is rendered as 'Month/Year' or 'Mm/YYYY' standard."
    }
  ]
}
```

### 2. Health Check Endpoint
- **URL**: `GET /health`
- **Description**: Verifies that the service is running.
- **Sample Response**:
```json
{
  "status": "healthy",
  "service": "Legal Metrology Compliance Rule Engine",
  "version": "1.0.0"
}
```

### Interactive API Documentation (Swagger / ReDoc)
- **Swagger UI**: `http://localhost:5002/docs`
- **ReDoc**: `http://localhost:5002/redoc`


