"""
Unit tests for LM-RULE-FONT-012: Font Size & Readability Rule.
"""

from app.models.product import EvaluateProductRequest
from app.models.rule_result import RuleStatus
from app.rules.font_height_rule import FontHeightRule


def test_font_height_pass():
    rule = FontHeightRule()
    product = EvaluateProductRequest(
        productId="PROD-001",
        fontSizeMm=2.5
    )
    res = rule.validate(product)
    assert res.status == RuleStatus.PASS


def test_font_height_too_small_fail():
    rule = FontHeightRule()
    product = EvaluateProductRequest(
        productId="PROD-002",
        fontSizeMm=0.5
    )
    res = rule.validate(product)
    assert res.status == RuleStatus.FAIL


def test_font_height_missing_manual_review():
    rule = FontHeightRule()
    product = EvaluateProductRequest(
        productId="PROD-003",
        fontSizeMm=None
    )
    res = rule.validate(product)
    assert res.status == RuleStatus.MANUAL_REVIEW
