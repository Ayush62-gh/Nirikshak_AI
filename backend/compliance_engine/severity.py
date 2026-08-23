import enum
from typing import Dict


class Severity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


DEFAULT_SEVERITY_WEIGHTS: Dict[Severity, int] = {
    Severity.CRITICAL: 20,
    Severity.HIGH: 15,
    Severity.MEDIUM: 10,
    Severity.LOW: 5,
    Severity.INFO: 0,
}
