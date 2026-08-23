"""
Base Rule Registry helpers.
"""

from typing import List, Type
from app.core.interface import AbstractRule


class RuleRegistry:
    """Registry maintaining all available Legal Metrology rules."""

    _registered_rules: List[Type[AbstractRule]] = []

    @classmethod
    def register(cls, rule_class: Type[AbstractRule]):
        """
        Decorator to automatically register a new rule class into the engine.
        Usage:
            @RuleRegistry.register
            class MyCustomRule(AbstractRule):
                ...
        """
        if rule_class not in cls._registered_rules:
            cls._registered_rules.append(rule_class)
        return rule_class

    @classmethod
    def get_all_rules(cls) -> List[AbstractRule]:
        """Instantiates and returns all registered rules."""
        return [rule_cls() for rule_cls in cls._registered_rules]

    @classmethod
    def clear(cls):
        """Clears registered rules (used for testing)."""
        cls._registered_rules.clear()

