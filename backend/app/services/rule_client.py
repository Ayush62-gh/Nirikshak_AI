import uuid
import asyncio
import httpx
from app.core.config import settings
from app.core.errors import ExternalServiceError, ExternalServiceRateLimitError


def _build_rule_engine_request(extracted_fields: dict) -> dict:
    mfg_date_str = extracted_fields.get("mfg_date") if isinstance(extracted_fields, dict) else None
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

    extracted = extracted_fields if isinstance(extracted_fields, dict) else {}
    product_id = extracted.get("product_id") or str(uuid.uuid4())

    return {
        "productId": product_id,
        "productName": extracted.get("product_name"),
        # TODO: Should eventually come from OCR or user input; hardcoded "food" for MVP
        "productType": "food",
        # TODO: Should eventually be detected/provided; hardcoded False for MVP
        "isImported": False,
        "manufacturerName": extracted.get("manufacturer"),
        "manufacturerAddress": extracted.get("manufacturer_address"),
        "packerName": None,
        "importerName": None,
        "netQuantity": extracted.get("net_quantity"),
        "mrp": extracted.get("mrp"),
        "monthOfPacking": month_of_packing,
        "yearOfPacking": year_of_packing,
        "consumerCare": extracted.get("consumer_care"),
        # TODO: Hardcoded assumption for MVP, should come from OCR/detection eventually
        "countryOfOrigin": "India",
    }


def _parse_rule_engine_response(response: dict) -> dict:
    if not isinstance(response, dict):
        raise ExternalServiceError("Rule Engine returned non-dict response format.")

    overall_status = str(response.get("overallStatus", "")).upper()
    status_map = {
        "PASS": "COMPLIANT",
        "FAIL": "NON_COMPLIANT",
        "MANUAL_REVIEW": "PARTIAL",
    }
    internal_status = status_map.get(overall_status, "PARTIAL")

    raw_violations = response.get("violations", [])
    if not isinstance(raw_violations, list):
        raw_violations = []

    violations = []
    for v in raw_violations:
        if not isinstance(v, dict):
            continue
        rule_name = v.get("ruleName") or v.get("ruleId") or "RULE_CHECK"
        message = v.get("message") or v.get("description") or ""
        remediation = v.get("remediation")
        if remediation:
            clean_message = str(message).rstrip(" .")
            message = f"{clean_message}. Suggested fix: {remediation}" if clean_message else f"Suggested fix: {remediation}"

        violations.append({
            "rule": str(rule_name),
            "description": str(message),
            "field": str(v.get("field") or "label"),
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

    timeout = httpx.Timeout(30.0, connect=5.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            res = await client.post(endpoint_url, json=payload)
            if res.status_code == 429:
                retry_after = res.headers.get("Retry-After")
                raise ExternalServiceRateLimitError(
                    detail="Rule Engine service rate limit exceeded",
                    retry_after=retry_after
                )
            res.raise_for_status()
            data = res.json()
            return _parse_rule_engine_response(data)
    except ExternalServiceRateLimitError:
        raise
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError) as err:
        raise ExternalServiceError(f"Rule Engine service request failed: {str(err)}") from err

