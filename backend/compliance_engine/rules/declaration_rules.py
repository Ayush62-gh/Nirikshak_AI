from typing import Any, Dict, Optional
from compliance_engine.rules.base_rule import BaseRule, RuleResult, RuleStatus
from compliance_engine.severity import Severity


class GenericCommodityRule(BaseRule):
    """
    Legal Metrology Rule 6(1)(b):
    Every package must declare generic/common name of the commodity contained in the package.
    """

    def evaluate(
        self, declarations: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        # Check either product_name or context product_name
        prod_name = declarations.get("product_name") or (context.get("product_name") if context else None)

        if not prod_name:
            return RuleResult(
                rule_id=self.rule_id,
                rule_number=self.rule_number,
                name=self.name,
                category=self.category,
                status=RuleStatus.WARNING,
                severity=self.severity,
                weight=self.weight,
                message="Generic commodity or product name is not prominently identified.",
                detected_value=None,
                expected_value="Generic / common name of commodity",
                legal_reference=self.legal_reference,
            )

        val = getattr(prod_name, "extracted_value", str(prod_name))
        return RuleResult(
            rule_id=self.rule_id,
            rule_number=self.rule_number,
            name=self.name,
            category=self.category,
            status=RuleStatus.PASS,
            severity=self.severity,
            weight=self.weight,
            message="Generic commodity name declared.",
            detected_value=val,
            expected_value="Commodity name",
            legal_reference=self.legal_reference,
        )
