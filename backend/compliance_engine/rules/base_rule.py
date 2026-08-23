from abc import ABC, abstractmethod
from dataclasses import dataclass
import enum
from typing import Any, Dict, Optional
from compliance_engine.severity import Severity


class RuleStatus(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class RuleResult:
    rule_id: str
    name: str
    category: str
    status: RuleStatus
    severity: Severity
    weight: int
    message: str
    rule_number: Optional[str] = None
    detected_value: Optional[str] = None
    expected_value: Optional[str] = None
    legal_reference: Optional[str] = None
    evidence_image: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_number": self.rule_number,
            "name": self.name,
            "category": self.category,
            "status": self.status.value,
            "severity": self.severity.value,
            "weight": self.weight,
            "message": self.message,
            "detected_value": self.detected_value,
            "expected_value": self.expected_value,
            "legal_reference": self.legal_reference,
            "evidence_image": self.evidence_image,
        }


class BaseRule(ABC):
    """Abstract base class for all Legal Metrology compliance rules."""

    def __init__(self, rule_config: Dict[str, Any]):
        self.rule_id = rule_config.get("rule_id", "UNKNOWN")
        self.rule_number = rule_config.get("rule_number", "")
        self.name = rule_config.get("name", "Unnamed Rule")
        self.category = rule_config.get("category", "GENERAL")
        self.field = rule_config.get("field", "")
        self.required = rule_config.get("required", True)
        self.severity = Severity(rule_config.get("severity", "HIGH"))
        self.weight = int(rule_config.get("weight", 10))
        self.active = rule_config.get("active", True)
        self.legal_reference = rule_config.get("legal_reference", "")
        self.description = rule_config.get("description", "")

    @abstractmethod
    def evaluate(
        self, declarations: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        """
        Evaluate declaration data against the rule.
        declarations: mapping of declaration_type -> ExtractedDeclaration / dict
        context: additional inspection / product context
        """
        pass
