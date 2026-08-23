"""
API Router Dependencies.
"""

from app.core.engine import RuleEngine

def get_rule_engine() -> RuleEngine:
    """Provides a RuleEngine instance for route injection."""
    return RuleEngine()
