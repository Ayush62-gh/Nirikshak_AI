import uuid
import asyncio
import httpx
from app.core.config import settings
from app.core.errors import ExternalServiceError


def _build_rule_engine_request(extracted_fields: dict) -> dict:
    mfg_date_str = extracted_fields.get("mfg_date")
    month_of_packing = None
    year_of_packing = None

    if mfg_date_str and isinstance(mfg_date_str, str):
        parts = mfg_date_str.replace("-", "/").split("/")
        if len(parts) == 2:
            p1, p2 = parts[0].strip(), parts[1].strip()
            if len(p1) == 2 and len(p2) == 4:  # MM/YYYY
                month_of_packing, year_of_packing = p1, p2
            elif len(p1) == 4 and len(p2) == 2:  # YYYY/MM
                month_of_packing, year_of_packing = p2, p1

    product_id = extracted_fields.get("product_id") or str(uuid.uuid4())

    return {
        "productId": product_id,
        "productName": extracted_fields.get("product_name"),
        # TODO: Should eventually come from OCR or user input; hardcoded "food" for MVP
        "productType": "food",
        # TODO: Should eventually be detected/provided; hardcoded False for MVP
        "isImported": False,
        "manufacturerName": extracted_fields.get("manufacturer"),
        # TODO: OCR does not currently extract manufacturerAddress
        "manufacturerAddress": None,
        "packerName": None,
        "importerName": None,
        "netQuantity": extracted_fields.get("net_quantity"),
        "mrp": extracted_fields.get("mrp"),
        "monthOfPacking": month_of_packing,
        "yearOfPacking": year_of_packing,
        "consumerCare": extracted_fields.get("consumer_care"),
        # TODO: Hardcoded assumption for MVP, should come from OCR/detection eventually
        "countryOfOrigin": "India",
    }


def _parse_rule_engine_response(response: dict) -> dict:
    overall_status = response.get("overallStatus", "").upper()
    status_map = {
        "PASS": "COMPLIANT",
        "FAIL": "NON_COMPLIANT",
        "MANUAL_REVIEW": "PARTIAL",
    }
    internal_status = status_map.get(overall_status, "PARTIAL")

    raw_violations = response.get("violations", [])
    violations = []
    for v in raw_violations:
        rule_name = v.get("ruleName") or v.get("ruleId") or "RULE_CHECK"
        message = v.get("message") or v.get("description") or ""
        remediation = v.get("remediation")
        if remediation:
            clean_message = message.rstrip(" .")
            message = f"{clean_message}. Suggested fix: {remediation}" if clean_message else f"Suggested fix: {remediation}"

        violations.append({
            "rule": rule_name,
            "description": message,
            "field": v.get("field") or "label",
        })

    return {
        "status": internal_status,
        "violations": violations,
    }


async def validate_compliance(extracted_fields: dict) -> dict:
    """
    Validates extracted label fields against Legal Metrology Packaged Commodities Rules.
    When use_mock_rule_engine is True, returns simulated mock response.
    When use_mock_rule_engine is False, calls external Rule Engine microservice at /api/v1/compliance/check.
    """
    if settings.use_mock_rule_engine:
        # Simulate network latency of Rule Engine service call
        await asyncio.sleep(0.1)

        return {
            "status": "PARTIAL",
            "violations": [
                {
                    "rule": "Rule 6",
                    "description": "Consumer care details format unclear",
                    "field": "consumer_care",
                }
            ],
        }

    # Live Rule Engine Integration
    payload = _build_rule_engine_request(extracted_fields)
    endpoint_url = f"{settings.RULE_ENGINE_URL.rstrip('/')}/api/v1/compliance/check"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(endpoint_url, json=payload)
            res.raise_for_status()
            data = res.json()
            return _parse_rule_engine_response(data)
    except (httpx.HTTPError, ValueError, KeyError) as err:
        raise ExternalServiceError(f"Rule Engine service request failed: {str(err)}") from err
