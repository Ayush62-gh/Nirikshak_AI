# Nirikshak AI

Nirikshak AI is a software system developed for checking the compliance of packaged commodities with the **Legal Metrology (Packaged Commodities) Rules, 2011**.

The main idea is to take a product or label image, extract the information from it using OCR, and then check the extracted information against predefined compliance rules.

## Problem

Checking packaged products manually can take a lot of time, especially when a large number of products have to be inspected.

Important details such as:

* Manufacturer / Packer / Importer details
* MRP
* Net quantity
* Manufacturing / packing information
* Other required declarations

need to be checked during inspection.

Nirikshak AI tries to make this process easier by automating the initial checking of these declarations.

## How it works

The basic flow of the system is:

```text
Product / Label Image
        ↓
     Upload
        ↓
    OCR/Paddle
        ↓
 Text Extraction
        ↓
 Field Extraction
        ↓
   Rule Checking
        ↓
 Compliance Result
        ↓
 Generate Report
```

The system can identify the information available on the package and pass it to the rule engine for validation.

## Main Features

* Upload product and label images
* Extract text using OCR (Paddle)
* Identify important product information
* Check mandatory declarations
* Detect missing or invalid information based on implemented rules
* Show compliance status
* Store inspection and product information
* View previous inspection records
* Generate compliance reports
* Dashboard for monitoring results
* Role-based access and authentication

## Project Structure

```text
Nirikshak_AI/
│
├── frontend/
├── backend/
├── ml_service/
├── rule_engine/
├── docs/
├── reports/
├── sample_images/
└── README.md
```

### Frontend

Contains the user interface of the application.

### Backend

Handles the application APIs, requests, database operations and communication between different services.

### ML Service

Handles the image and OCR related processing.

### Rule Engine

Contains the rules used for checking the extracted product information.

### Sample Images

Contains images that can be used for testing the system.

## Technology Used

* React
* FastAPI
* Python
* Paddle
* SQLite
* REST APIs

## Example

A product image is given as input to the system.

After OCR and extraction, the system can get information such as:

```text
MRP: ₹100
Net Quantity: 500 g
Manufacturer: ABC Foods Pvt. Ltd.
Consumer Care: 1800-XXXX-XXXX
```

The extracted information is then checked by the rule engine.

The result can contain:

```text
MRP                  ✓
Net Quantity         ✓
Manufacturer         ✓
Consumer Care        ✓
Required Declaration ✗
```

The system can then mark the product based on the checks implemented in the rule engine and provide the corresponding violation details.

## Rule Engine

The rule engine is responsible for checking the extracted information.

```text
OCR Data
   ↓
Required Field Check
   ↓
Value / Format Check
   ↓
Compliance Rules
   ↓
Result
```

Rules can be updated or extended as more compliance requirements are added to the system.

## Reports

The system is intended to generate digital reports containing information such as:

* Product details
* Extracted information
* Compliance status
* Detected violations
* Supporting images/evidence
* Inspection details

## Testing

Sample product and label images are used to test different situations, including:

* Complete product information
* Missing declarations
* Incorrect information
* Poor quality images
* Different label layouts

## Future Improvements

Some possible improvements are:

* Better OCR accuracy
* Support for more Indian languages
* More detailed font-size and readability checking
* Automatic updating of compliance rules
* Mobile application
* Better analytics and dashboards
* Cloud deployment
* Integration with product listings

## Problem Statement

**SIH Problem Statement ID:** 26034

**Problem Statement:** Software System to check compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011 by scanning products, images and labels.

**Department:** Department of Consumer Affairs
**Ministry:** Ministry of Consumer Affairs, Food & Public Distribution

## Team

Nirikshak AI was developed as a Smart India Hackathon project.
