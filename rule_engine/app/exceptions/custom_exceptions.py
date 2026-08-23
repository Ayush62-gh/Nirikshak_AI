"""
Custom Exception Classes for the Legal Metrology Compliance Rule Engine.
"""

class RuleEngineBaseException(Exception):
    """Base exception for all Rule Engine errors."""
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class ProductDataValidationError(RuleEngineBaseException):
    """Raised when incoming product payload fails validation checks."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message=message, status_code=400, details=details)


class RuleExecutionError(RuleEngineBaseException):
    """Raised when an error occurs during individual rule execution."""
    def __init__(self, rule_id: str, message: str, details: dict = None):
        super().__init__(
            message=f"Execution error in rule [{rule_id}]: {message}",
            status_code=500,
            details=details
        )
        self.rule_id = rule_id


class RuleNotFoundError(RuleEngineBaseException):
    """Raised when a requested rule ID cannot be located."""
    def __init__(self, rule_id: str):
        super().__init__(
            message=f"Rule with ID '{rule_id}' was not found in registry.",
            status_code=4404
        )
        self.rule_id = rule_id
