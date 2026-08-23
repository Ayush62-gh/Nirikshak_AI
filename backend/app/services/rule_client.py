import asyncio
import httpx
from app.core.config import settings


async def validate_compliance(extracted_fields: dict) -> dict:
    """
    Validates extracted label fields against Legal Metrology Packaged Commodities Rules.
    Currently mocked to simulate rule_engine service behavior.
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

    # REAL SERVICE INTEGRATION (Future Phase Ready)
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{settings.RULE_ENGINE_URL}/validate", json=extracted_fields)
        response.raise_for_status()
        return response.json()
