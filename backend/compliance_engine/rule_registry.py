import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from app.core.config import settings
from app.core.logging import logger
from compliance_engine.rules import (
    BaseRule,
    ConsumerCareEmailRule,
    ConsumerCarePhoneRule,
    DateDeclarationRule,
    GenericCommodityRule,
    ImporterRule,
    ManufacturerRule,
    MRPRule,
    NetQuantityRule,
    PhysicalFontSizeRule,
    ReadabilityRule,
)


class RuleRegistry:
    """Registry that manages active Legal Metrology rules and handler instantiation."""

    # Default mapping of field/category to Rule class implementations
    HANDLER_MAPPING: Dict[str, Type[BaseRule]] = {
        "mrp": MRPRule,
        "net_quantity": NetQuantityRule,
        "mfg_date": DateDeclarationRule,
        "pkd_date": DateDeclarationRule,
        "manufacturer": ManufacturerRule,
        "packer": ManufacturerRule,
        "consumer_care_email": ConsumerCareEmailRule,
        "consumer_care_phone": ConsumerCarePhoneRule,
        "country_of_origin": ImporterRule,
        "importer": ImporterRule,
        "product_name": GenericCommodityRule,
        "readability": ReadabilityRule,
        "font_size": PhysicalFontSizeRule,
    }

    @classmethod
    def load_rules_from_json(cls, file_path: Optional[Path] = None) -> List[BaseRule]:
        """Load and instantiate active rules from JSON configuration."""
        path = file_path or settings.rules_path
        if not path.exists():
            logger.warning(f"Rules configuration file not found at {path}")
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                rules_data: List[Dict[str, Any]] = json.load(f)

            instantiated_rules: List[BaseRule] = []
            for item in rules_data:
                if not item.get("active", True):
                    continue

                field = item.get("field", "").lower()
                category = item.get("category", "").lower()
                rule_id = item.get("rule_id", "")

                rule_cls = (
                    cls.HANDLER_MAPPING.get(field)
                    or cls.HANDLER_MAPPING.get(category)
                    or BaseRule
                )

                if rule_cls is not BaseRule:
                    instantiated_rules.append(rule_cls(item))
                else:
                    logger.warning(f"No specific handler class for rule {rule_id} (field={field})")

            logger.info(f"Loaded {len(instantiated_rules)} active Legal Metrology rules from {path}")
            return instantiated_rules

        except Exception as e:
            logger.error(f"Failed to load rules from {path}: {e}")
            return []
