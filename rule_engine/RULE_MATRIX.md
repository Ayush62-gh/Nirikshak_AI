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

> **Note**: Legal references abhi official Rules text se verify hone baaki hain.

Active statutory rules that evaluate structured product JSON payloads and populate standardized result DTOs containing `ruleId`, `ruleName`, `status`, `severity`, `message`, `field`, and `evidence`.

### 1. `LM-RULE-MRP-001`: Maximum Retail Price (MRP) Declaration Check
- **Rule ID**: `LM-RULE-MRP-001`
- **Rule Name**: Maximum Retail Price (MRP) Declaration Check
- **Target Field**: `mrp`
- **Legal Reference**: Rule 6(1)(e) & Rule 2(m) [VERIFY against official Rules text], Legal Metrology (Packaged Commodities) Rules, 2011.
- **Applicability**: Applies to all retail packaged commodities.
- **Required Input**: `mrp` (string)
- **PASS Behavior**: Returns `PASS` when numeric digits AND a statutory tax inclusion phrase (`incl. of all taxes` / `inclusive of all taxes` or Hindi equivalents like `सब कर सहित`, `सभी करों सहित`, `कर सहित`, `कर सहित मूल्य`) are present. Explicit currency symbol/words (`₹`, `Rs`, `INR`, `mrp`, `रु`, `रू`, `मूल्य`) are checked but digits + tax clause is sufficient.
- **FAIL Behavior**: Returns `FAIL` when `mrp` is completely missing, empty, or contains no numeric price value.
- **MANUAL_REVIEW Behavior**: Returns `MANUAL_REVIEW` when numeric price digits are present, but statutory tax inclusion phrase (`incl. of all taxes`) is missing.
- **NOT_APPLICABLE Behavior**: N/A (Applies universally to retail packaged goods).
- **Severity**: **CRITICAL**
> **Known Limitation**: Code permits passing MRP validation based on numeric digits and tax clause without strictly requiring a standard currency symbol ('₹' or 'Rs'). [VERIFY against official Rules text]

---

### 2. `LM-RULE-NETQTY-002`: Net Quantity Declaration Check
- **Rule ID**: `LM-RULE-NETQTY-002`
- **Rule Name**: Net Quantity Declaration Check
- **Target Field**: `netQuantity`
- **Legal Reference**: Rule 6(1)(c), Rule 11 & Rule 12 [VERIFY against official Rules text], Legal Metrology (Packaged Commodities) Rules, 2011.
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
- **Legal Reference**: Rule 6(1)(a) [VERIFY against official Rules text], Legal Metrology (Packaged Commodities) Rules, 2011.
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
- **Legal Reference**: Rule 6(1)(b) [VERIFY against official Rules text], Legal Metrology (Packaged Commodities) Rules, 2011.
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
- **Legal Reference**: Rule 6(1)(a) [VERIFY against official Rules text], Legal Metrology (Packaged Commodities) Rules, 2011.
- **Applicability**: Applies to all domestic packaged commodities (`isImported != True`) or where manufacturer details are specified.
- **Required Input**: `manufacturerName` (string), `packerName` (string), `isImported` (boolean)
- **PASS Behavior**: Returns `PASS` when `manufacturerName` or `packerName` declaration is present in structured payload.
- **FAIL Behavior**: Returns `FAIL` when both `manufacturerName` AND `packerName` are missing on a domestic package payload.
- **MANUAL_REVIEW Behavior**: N/A.
- **NOT_APPLICABLE Behavior**: Returns `NOT_APPLICABLE` when product is explicitly imported (`isImported == True`) and no manufacturer details are specified.
- **Severity**: **CRITICAL**

---

### 6. `LM-RULE-MFGADDR-006`: Manufacturer or Packer Address Declaration Check
- **Rule ID**: `LM-RULE-MFGADDR-006`
- **Rule Name**: Manufacturer or Packer Address Declaration Check
- **Target Field**: `manufacturerAddress`
- **Legal Reference**: Rule 6(1)(a) [VERIFY against official Rules text], Legal Metrology (Packaged Commodities) Rules, 2011.
- **Applicability**: Applies to all domestic packages (`isImported != True`) or where manufacturer details are specified.
- **Required Input**: `manufacturerAddress` (string), `isImported` (boolean)
- **PASS Behavior**: Returns `PASS` when `manufacturerAddress` text contains a 6-digit Indian postal pincode.
- **FAIL Behavior**: Returns `FAIL` when `manufacturerAddress` is completely missing or empty string.
- **MANUAL_REVIEW Behavior**: Returns `MANUAL_REVIEW` when `manufacturerAddress` text is present but lacks a 6-digit Indian pincode.
- **NOT_APPLICABLE Behavior**: Returns `NOT_APPLICABLE` when product is explicitly imported (`isImported == True`) and no manufacturer address is specified.
- **Severity**: **HIGH**
> **Known Limitation**: 6-digit numbers in address text (such as batch or licence numbers) may be incorrectly matched as postal pincodes.

---

### 7. `LM-RULE-DATE-007`: Month and Year of Packing / Manufacture Check
- **Rule ID**: `LM-RULE-DATE-007`
- **Rule Name**: Month and Year of Packing / Manufacture Check
- **Target Field**: `monthOfPacking`
- **Legal Reference**: Rule 6(1)(d) [VERIFY against official Rules text], Legal Metrology (Packaged Commodities) Rules, 2011.
- **Applicability**: Applies to all retail packaged commodities.
- **Required Input**: `monthOfPacking` (string), `yearOfPacking` (string)
- **PASS Behavior**: Returns `PASS` when both Month AND Year of packing are declared in valid standard formats.
- **FAIL Behavior**: Returns `FAIL` when both Month and Year are missing, OR only one of Month/Year is provided.
- **MANUAL_REVIEW Behavior**: Returns `MANUAL_REVIEW` when Month or Year format is non-standard.
- **NOT_APPLICABLE Behavior**: N/A (Applies universally to retail packages).
- **Severity**: **HIGH**

---

### 8. `LM-RULE-CARE-008`: Consumer Care Details Declaration Check
- **Rule ID**: `LM-RULE-CARE-008`
- **Rule Name**: Consumer Care Details Declaration Check
- **Target Field**: `consumerCare`
- **Legal Reference**: Rule 6(1)(h) & Rule 6(2) [VERIFY against official Rules text], Legal Metrology (Packaged Commodities) Rules, 2011.
- **Applicability**: Applies to all retail packaged commodities.
- **Required Input**: `consumerCare` (string)
- **PASS Behavior**: Returns `PASS` when consumer care contact details (phone/email/address) are declared.
- **FAIL Behavior**: Returns `FAIL` when `consumerCare` contact details are completely missing.
- **MANUAL_REVIEW Behavior**: Returns `MANUAL_REVIEW` when text is provided but lacks clear telephone or email contact format.
- **NOT_APPLICABLE Behavior**: N/A (Applies universally to retail packages).
- **Severity**: **HIGH**

---

### 9. `LM-RULE-COO-009`: Country of Origin Declaration Check
- **Rule ID**: `LM-RULE-COO-009`
- **Rule Name**: Country of Origin Declaration Check
- **Target Field**: `countryOfOrigin`
- **Legal Reference**: Rule 6(1)(ab) [VERIFY against official Rules text], Legal Metrology (Packaged Commodities) Rules, 2011.
- **Applicability**: Applies to imported commodities (`isImported == True`) or when `countryOfOrigin` input is supplied.
- **Required Input**: `isImported` (boolean), `countryOfOrigin` (string)
- **PASS Behavior**: Returns `PASS` when `countryOfOrigin` string is non-empty.
- **FAIL Behavior**: Returns `FAIL` when `isImported == True` and `countryOfOrigin` is missing or empty.
- **MANUAL_REVIEW Behavior**: Returns `MANUAL_REVIEW` when `countryOfOrigin` is missing and import status is unconfirmed (`isImported == None`).
- **NOT_APPLICABLE Behavior**: Returns `NOT_APPLICABLE` when product is explicitly domestic (`isImported == False`) and `countryOfOrigin` is unprovided.
- **Severity**: **CRITICAL**

---

### 10. `LM-RULE-USP-010`: Unit Sale Price (USP) Declaration Check
- **Rule ID**: `LM-RULE-USP-010`
- **Rule Name**: Unit Sale Price (USP) Declaration Check
- **Target Field**: `unitSalePrice`
- **Legal Reference**: Rule 6(11) [VERIFY against official Rules text], Legal Metrology (Packaged Commodities) Rules, 2011 (2021 DoCA Amendment).
- **Applicability**: Applies when `unitSalePrice` is provided, USP pattern is detected in `mrp`, OR `netQuantity` contains numeric digits.
- **Required Input**: `unitSalePrice` (string), `mrp` (string), `netQuantity` (string)
- **PASS Behavior**: Returns `PASS` when standard USP pattern (e.g. `Rs 0.50/g`, `₹200/kg`) is detected in `unitSalePrice` or embedded in `mrp`.
- **FAIL Behavior**: N/A (Missing USP currently triggers `MANUAL_REVIEW` pending statutory applicability threshold verification).
- **MANUAL_REVIEW Behavior**: Returns `MANUAL_REVIEW` when `unitSalePrice` text is non-standard, OR when `unitSalePrice` is missing but `netQuantity` is present.
- **NOT_APPLICABLE Behavior**: Returns `NOT_APPLICABLE` when neither `unitSalePrice` nor numeric `netQuantity` is supplied.
- **Severity**: **HIGH**

---

### 11. `LM-RULE-EXP-011`: Best Before / Expiry Date Declaration Check
- **Rule ID**: `LM-RULE-EXP-011`
- **Rule Name**: Best Before / Expiry Date Declaration Check
- **Target Field**: `expiryDate`
- **Legal Reference**: Rule 6(1)(d) [VERIFY against official Rules text], Legal Metrology (Packaged Commodities) Rules, 2011 & FSSAI Guidelines.
- **Applicability**: Applies to perishable product types (`food`, `cosmetics`, `pharma`, etc.) OR when `expiryDate` is supplied.
- **Required Input**: `productType` (string), `expiryDate` (string)
- **PASS Behavior**: Returns `PASS` when valid expiry format (e.g. `Best Before 12 Months`, `Exp: 12/2027`, `08/2026`) is present.
- **FAIL Behavior**: Returns `FAIL` when perishable product lacks expiry date declaration.
- **MANUAL_REVIEW Behavior**: Returns `MANUAL_REVIEW` when `expiryDate` text is non-standard or unparseable (e.g. `abc`, `99/2027`), OR when product type is unconfirmed.
- **NOT_APPLICABLE Behavior**: Returns `NOT_APPLICABLE` when product is non-perishable and lacks expiry date declaration.
- **Severity**: **HIGH**

---

### 12. `LM-RULE-FONT-012`: Font Size & Readability Analysis Check
- **Rule ID**: `LM-RULE-FONT-012`
- **Rule Name**: Font Size & Readability Analysis Check
- **Target Field**: `fontSizeMm`
- **Legal Reference**: Rule 7 & Rule 9 [VERIFY against official Rules text], Legal Metrology (Packaged Commodities) Rules, 2011.
- **Applicability**: Applies ONLY when physical font height measurement (`fontSizeMm`) is supplied in request payload.
- **Required Input**: `fontSizeMm` (float)
- **PASS Behavior**: Returns `PASS` when `fontSizeMm >= 1.0` mm.
- **FAIL Behavior**: Returns `FAIL` when `fontSizeMm < 1.0` mm.
- **MANUAL_REVIEW Behavior**: Returns `MANUAL_REVIEW` when `fontSizeMm` measurement is missing/unprovided when called directly.
- **NOT_APPLICABLE Behavior**: Returns `NOT_APPLICABLE` when `fontSizeMm` is not supplied in product payload.
- **Severity**: **HIGH**

---

### 13. `LM-RULE-PLACE-013`: Declaration Placement & PDP Panel Check
- **Rule ID**: `LM-RULE-PLACE-013`
- **Rule Name**: Declaration Placement & PDP Panel Check
- **Target Field**: `declarationPlacement`
- **Legal Reference**: Rule 6 & Rule 7 [VERIFY against official Rules text], Legal Metrology (Packaged Commodities) Rules, 2011.
- **Applicability**: Applies when `declarationPlacement` text OR `isPDPPlacementValid` boolean is supplied in request payload.
- **Required Input**: `declarationPlacement` (string), `isPDPPlacementValid` (boolean)
- **PASS Behavior**: Returns `PASS` when `isPDPPlacementValid == True` OR placement text indicates Principal Display Panel / Front Panel.
- **FAIL Behavior**: Returns `FAIL` when `isPDPPlacementValid == False`.
- **MANUAL_REVIEW Behavior**: Returns `MANUAL_REVIEW` when placement text location requires manual verification.
- **NOT_APPLICABLE Behavior**: Returns `NOT_APPLICABLE` when placement metadata is not supplied in request payload.
- **Severity**: **HIGH**

---

### 14. `LM-RULE-READ-014`: Physical Legibility & Color Contrast Check
- **Rule ID**: `LM-RULE-READ-014`
- **Rule Name**: Physical Legibility & Color Contrast Check
- **Target Field**: `contrastRatio`
- **Legal Reference**: Rule 8 [VERIFY against official Rules text], Legal Metrology (Packaged Commodities) Rules, 2011.
- **Applicability**: Applies when `contrastRatio` float measurement OR `isLegible` boolean is supplied in request payload.
- **Required Input**: `contrastRatio` (float), `isLegible` (boolean)
- **PASS Behavior**: Returns `PASS` when `contrastRatio >= 4.5` OR `isLegible == True`.
- **FAIL Behavior**: Returns `FAIL` when `contrastRatio < 3.0` OR `isLegible == False`.
- **MANUAL_REVIEW Behavior**: Returns `MANUAL_REVIEW` when contrast ratio is between 3.0 and 4.5.
- **NOT_APPLICABLE Behavior**: Returns `NOT_APPLICABLE` when contrast metadata is not supplied in request payload.
- **Severity**: **HIGH**

---

## B. RULES REQUIRING ADDITIONAL INPUT

Rules requiring additional structured metadata fields before automated machine evaluation can be executed.

*(None currently. All supported rules evaluate structured request payloads directly).*

---

## C. RULES REQUIRING IMAGE OR PHYSICAL LABEL ANALYSIS

Physical label and visual parameters that cannot be proven solely by text strings in structured JSON payloads and currently return `MANUAL_REVIEW` where applicable:

- **Physical Package Surface Dimensions**: Overall surface area calculations.

---

## D. RULES PENDING LEGAL / APPLICABILITY CONFIGURATION

Pending statutory rules documented for future implementation:

*(None currently pending. All active statutory rules have been integrated into Section A).*
