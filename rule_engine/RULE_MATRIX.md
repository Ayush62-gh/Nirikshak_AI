# Statutory Legal Metrology Compliance Rule Matrix

This document provides a production-grade statutory mapping and evidence provenance specification for the **Legal Metrology Compliance Rule Engine** based on the **Legal Metrology (Packaged Commodities) Rules, 2011** (as amended).

---

## 🔬 Evidence & Provenance Architecture

### 1. Separation of Extracted Evidence from Statutory Compliance Decisions
The rule engine enforces a strict architectural boundary between data extraction (what was detected) and statutory evaluation (what the rule concludes):

$$\text{AI / OCR Detection} \xrightarrow{\text{Evidence Provenance}} \text{Structured Input} \xrightarrow{\text{Deterministic Rules}} \text{Compliance Outcome}$$

- **AI/OCR Extraction**: Identifies label text snippets, bounding boxes, and extraction confidence scores ($0.0 \le \text{confidence} \le 1.0$).
- **Rule Engine**: Evaluates whether the extracted evidence satisfies mandatory legal provisions. High extraction confidence (e.g. `confidence = 0.99`) does **NOT** override statutory rule logic or force a false `PASS`.

### 2. Evidence Source Types (`EvidenceSource`)
- `STRUCTURED_INPUT`: Direct API payload inputs from upstream backend services or database records (default).
- `OCR`: Optical Character Recognition extracted text snippets from physical package label scans.
- `IMAGE_ANALYSIS`: Computer vision or multimodal image model findings.
- `USER_INPUT`: Manual entry or override data from human compliance officers.
- `UNKNOWN`: Unspecified or unverified data source.

### 3. Confidence Metadata
- Extraction confidence is represented as a normalized floating-point score ($0.0 \le \text{confidence} \le 1.0$).
- Confidence serves strictly as supporting metadata for audit trails and human reviewer context. It is **never** used as an automated compliance decision threshold.

### 4. Input Validation & Status Aggregation Precedence
The rule engine computes overall product compliance using strict deterministic status precedence:
$$\text{FAIL} \succ \text{MANUAL\_REVIEW} \succ \text{PASS} \succ \text{NOT\_APPLICABLE}$$

- **Overall `FAIL`**: Triggered if **at least 1** applicable rule returns `FAIL`.
- **Overall `MANUAL_REVIEW`**: Triggered if **0** rules fail, but **at least 1** applicable rule returns `MANUAL_REVIEW`.
- **Overall `PASS`**: Triggered if **0** rules fail or need manual review, and **at least 1** applicable rule returns `PASS`.
- **Overall `NOT_APPLICABLE`**: Triggered if **100%** of evaluated rules return `NOT_APPLICABLE`.

---

## A. VERIFIED MACHINE-CHECKABLE RULES

Active statutory rules that evaluate structured product JSON payloads and populate standardized result DTOs containing `ruleId`, `ruleName`, `status`, `severity`, `message`, `field`, and `evidence`.

### 1. `LM-RULE-MRP-001`: Maximum Retail Price (MRP) Declaration Check
- **Rule ID**: `LM-RULE-MRP-001`
- **Rule Name**: Maximum Retail Price (MRP) Declaration Check
- **Target Field**: `mrp`
- **Legal Reference**: Rule 6(1)(e) & Rule 2(m), Legal Metrology (Packaged Commodities) Rules, 2011.
- **Applicability**: Applies to all retail packaged commodities.
- **Required Input**: `mrp` (string)
- **PASS Behavior**: Returns `PASS` when numeric price, currency symbol/indicator (`₹`, `Rs`, `INR`), AND statutory tax inclusion phrase (`incl. of all taxes` / `inclusive of all taxes`) are clearly present in structured data.
- **FAIL Behavior**: Returns `FAIL` when `mrp` is completely missing, empty, or contains no numeric price value.
- **MANUAL_REVIEW Behavior**: Returns `MANUAL_REVIEW` when a numeric price value is present, but statutory presentation layout or tax inclusion clause (`incl. of all taxes`) cannot be verified from structured input.
- **NOT_APPLICABLE Behavior**: N/A (Applies universally to retail packaged goods).
- **Severity**: **CRITICAL**

---

### 2. `LM-RULE-NETQTY-002`: Net Quantity Declaration Check
- **Rule ID**: `LM-RULE-NETQTY-002`
- **Rule Name**: Net Quantity Declaration Check
- **Target Field**: `netQuantity`
- **Legal Reference**: Rule 6(1)(c), Rule 11 & Rule 12, Legal Metrology (Packaged Commodities) Rules, 2011.
- **Applicability**: Applies to all packaged commodities.
- **Required Input**: `netQuantity` (string)
- **PASS Behavior**: Returns `PASS` when numeric quantity AND a valid statutory metric unit matching standard categories (`WEIGHT`, `VOLUME`, `LENGTH`, `AREA`, `NUMBER_OR_UNIT`) are present.
- **FAIL Behavior**: Returns `FAIL` when `netQuantity` is completely missing, empty, or lacks numeric quantity digits.
- **MANUAL_REVIEW Behavior**: Returns `MANUAL_REVIEW` when a numeric quantity is present, but unit symbol or category alignment cannot be categorized from available input.
- **NOT_APPLICABLE Behavior**: N/A (Applies universally to packaged goods).
- **Severity**: **HIGH**

---

### 3. `LM-RULE-IMP-003`: Importer Name & Address Check for Foreign Commodities
- **Rule ID**: `LM-RULE-IMP-003`
- **Rule Name**: Importer Name & Address Check for Foreign Commodities
- **Target Field**: `importerName`
- **Legal Reference**: Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011.
- **Applicability**: Evaluated directly against `isImported == True`.
- **Required Input**: `isImported` (boolean), `importerName` (string)
- **PASS Behavior**: Returns `PASS` when `isImported == True` and importer name/details are declared.
- **FAIL Behavior**: Returns `FAIL` when `isImported == True` and `importerName` is completely missing or empty.
- **MANUAL_REVIEW Behavior**: Returns `MANUAL_REVIEW` when `isImported` status is unconfirmed (`isImported == None`).
- **NOT_APPLICABLE Behavior**: Returns `NOT_APPLICABLE` when commodity is explicitly domestic (`isImported == False`).
- **Severity**: **CRITICAL**

---

### 4. `LM-RULE-NAME-004`: Generic / Commodity Name Declaration Check
- **Rule ID**: `LM-RULE-NAME-004`
- **Rule Name**: Generic / Commodity Name Declaration Check
- **Target Field**: `productName`
- **Legal Reference**: Rule 6(1)(b), Legal Metrology (Packaged Commodities) Rules, 2011.
- **Applicability**: Applies to all retail packaged commodities.
- **Required Input**: `productName` (string)
- **PASS Behavior**: Returns `PASS` when generic or common name of commodity is present in structured payload.
- **FAIL Behavior**: Returns `FAIL` when `productName` is completely missing or empty string.
- **MANUAL_REVIEW Behavior**: Returns `MANUAL_REVIEW` when commodity name text is vague, numeric-only, or < 2 characters.
- **NOT_APPLICABLE Behavior**: N/A (Applies universally to retail packaged goods).
- **Severity**: **HIGH**

---

### 5. `LM-RULE-MFGNAME-005`: Manufacturer or Packer Name Declaration Check
- **Rule ID**: `LM-RULE-MFGNAME-005`
- **Rule Name**: Manufacturer or Packer Name Declaration Check
- **Target Field**: `manufacturerName`
- **Legal Reference**: Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011.
- **Applicability**: Applies to all domestic packaged commodities (`isImported != True`) or where manufacturer details are specified.
- **Required Input**: `manufacturerName` (string), `packerName` (string), `isImported` (boolean)
- **PASS Behavior**: Returns `PASS` when `manufacturerName` or `packerName` declaration is clearly present in structured data.
- **FAIL Behavior**: Returns `FAIL` when both `manufacturerName` AND `packerName` are completely missing on a domestic package.
- **MANUAL_REVIEW Behavior**: Returns `MANUAL_REVIEW` when legal relationship or completeness cannot be determined from structured payload.
- **NOT_APPLICABLE Behavior**: Returns `NOT_APPLICABLE` when product is explicitly imported (`isImported == True`) and no manufacturer details are specified.
- **Severity**: **CRITICAL**

---

### 6. `LM-RULE-MFGADDR-006`: Manufacturer or Packer Address Declaration Check
- **Rule ID**: `LM-RULE-MFGADDR-006`
- **Rule Name**: Manufacturer or Packer Address Declaration Check
- **Target Field**: `manufacturerAddress`
- **Legal Reference**: Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011.
- **Applicability**: Applies to all domestic packages (`isImported != True`) or where manufacturer details are specified.
- **Required Input**: `manufacturerAddress` (string), `isImported` (boolean)
- **PASS Behavior**: Returns `PASS` when `manufacturerAddress` text is present in structured payload.
- **FAIL Behavior**: Returns `FAIL` when `manufacturerAddress` is completely missing or empty.
- **MANUAL_REVIEW Behavior**: Returns `MANUAL_REVIEW` when address text is present but physical label completeness cannot be determined.
- **NOT_APPLICABLE Behavior**: Returns `NOT_APPLICABLE` when product is explicitly imported (`isImported == True`) and no manufacturer address is specified.
- **Severity**: **HIGH**

---

### 7. `LM-RULE-DATE-007`: Month and Year of Packing / Manufacture Check
- **Rule ID**: `LM-RULE-DATE-007`
- **Rule Name**: Month and Year of Packing / Manufacture Check
- **Target Field**: `monthOfPacking`
- **Legal Reference**: Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011.
- **Applicability**: Applies to all retail packaged commodities.
- **Required Input**: `monthOfPacking` (string), `yearOfPacking` (string)
- **PASS Behavior**: Returns `PASS` when both Month AND Year of packing are declared in valid standard formats.
- **FAIL Behavior**: Returns `FAIL` when both Month and Year are missing, OR only one of Month/Year is provided.
- **MANUAL_REVIEW Behavior**: Returns `MANUAL_REVIEW` when Month or Year format is non-standard (e.g. invalid month name or unverified year digits).
- **NOT_APPLICABLE Behavior**: N/A (Applies universally to retail packages).
- **Severity**: **HIGH**

---

### 8. `LM-RULE-CARE-008`: Consumer Care Details Declaration Check
- **Rule ID**: `LM-RULE-CARE-008`
- **Rule Name**: Consumer Care Details Declaration Check
- **Target Field**: `consumerCare`
- **Legal Reference**: Rule 6(1)(h) & Rule 6(2), Legal Metrology (Packaged Commodities) Rules, 2011.
- **Applicability**: Applies to all retail packaged commodities.
- **Required Input**: `consumerCare` (string)
- **PASS Behavior**: Returns `PASS` when consumer care contact details (phone/email/address) are declared.
- **FAIL Behavior**: Returns `FAIL` when `consumerCare` contact details are completely missing.
- **MANUAL_REVIEW Behavior**: Returns `MANUAL_REVIEW` when text is provided but lacks clear telephone or email contact format.
- **NOT_APPLICABLE Behavior**: N/A (Applies universally to retail packages).
- **Severity**: **HIGH**

---

## B. RULES REQUIRING ADDITIONAL INPUT

Rules requiring additional structured metadata fields before automated machine evaluation can be executed.

1. **Country of Origin Rule (Rule 6(1)(ab))**:
   - *Status*: Architecture prepared as a separate standalone rule.
   - *Required Input*: `countryOfOrigin` string and `isImported` flag.
   - *Requirement*: Mandatory for imported goods under 2017/2020 Legal Metrology amendments.

---

## C. RULES REQUIRING IMAGE OR PHYSICAL LABEL ANALYSIS

Physical label and visual parameters that cannot be proven solely by text strings in structured JSON payloads and currently return `MANUAL_REVIEW` where applicable:

- **Font Size & Text Height (Rule 7 & Rule 9)**: Minimum physical font height in millimeters based on net quantity package area.
- **Declaration Placement & Principal Display Panel Layout (Rule 6 & Rule 7)**: Specific label panel positioning and prominence.
- **Physical Legibility & Color Contrast (Rule 8)**: Visual contrast between printed text and packaging background.
- **Physical Package Dimensions**: Overall surface area calculations.

---

## D. RULES PENDING LEGAL / APPLICABILITY CONFIGURATION

Pending statutory rules documented for future implementation:

1. **Unit Sale Price Rule (Rule 6(11) - 2021 Amendment)**:
   - *Status*: Pending separate implementation.
   - *Reason*: Requires configurable applicability logic, quantity basis, thresholds/exceptions, and applicable amendment/version handling. Must not be implemented using guessed thresholds.

2. **Best Before / Use By Declaration Rule**:
   - *Status*: Requires product-category and applicability information before implementation.
   - *Reason*: Mandatory for perishable commodities, food, cosmetics, and drugs, but exempted for long-shelf-life non-perishables. Not marked as an active rule.

3. **Country of Origin Rule (Rule 6(1)(ab))**:
   - *Status*: Prepared for separate future implementation as an independent rule.
