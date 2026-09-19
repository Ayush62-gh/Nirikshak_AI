"""
Unit tests for LM-RULE-EXP-011: Best Before / Expiry Date Declaration Rule.
"""

from app.models.product import EvaluateProductRequest
from app.models.rule_result import RuleStatus
from app.rules.expiry_date_rule import ExpiryDateRule


def test_expiry_pass():
    rule = ExpiryDateRule()
    product = EvaluateProductRequest(
        productId="PROD-001",
        productType="food",
        expiryDate="Best Before 12 Months"
    )
    res = rule.validate(product)
    assert res.status == RuleStatus.PASS


def test_expiry_perishable_missing_fail():
    rule = ExpiryDateRule()
    product = EvaluateProductRequest(
        productId="PROD-002",
        productType="food",
        expiryDate=None
    )
    res = rule.validate(product)
    assert res.status == RuleStatus.FAIL


def test_expiry_unconfirmed_manual_review():
    rule = ExpiryDateRule()
    product = EvaluateProductRequest(
        productId="PROD-003",
        productType=None,
        expiryDate=None
    )
    res = rule.validate(product)
    assert res.status == RuleStatus.MANUAL_REVIEW
