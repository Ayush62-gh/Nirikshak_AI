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


def test_expiry_pass_best_before_6_months():
    rule = ExpiryDateRule()
    product = EvaluateProductRequest(
        productId="PROD-001B",
        productType="food",
        expiryDate="Best Before 6 months"
    )
    res = rule.validate(product)
    assert res.status == RuleStatus.PASS


def test_expiry_invalid_text_abc_manual_review():
    rule = ExpiryDateRule()
    product = EvaluateProductRequest(
        productId="PROD-001C",
        productType="food",
        expiryDate="abc"
    )
    res = rule.validate(product)
    assert res.status == RuleStatus.MANUAL_REVIEW


def test_expiry_invalid_month_manual_review():
    rule = ExpiryDateRule()
    product = EvaluateProductRequest(
        productId="PROD-001D",
        productType="food",
        expiryDate="99/2027"
    )
    res = rule.validate(product)
    assert res.status == RuleStatus.MANUAL_REVIEW


def test_expiry_perishable_missing_fail():
    rule = ExpiryDateRule()
    product = EvaluateProductRequest(
        productId="PROD-002",
        productType="food",
        expiryDate=None
    )
    res = rule.validate(product)
    assert res.status == RuleStatus.FAIL


def test_expiry_perishable_empty_string_fail():
    rule = ExpiryDateRule()
    product = EvaluateProductRequest(
        productId="PROD-002B",
        productType="food",
        expiryDate=""
    )
    res = rule.validate(product)
    assert res.status == RuleStatus.FAIL


def test_expiry_non_perishable_empty_not_applicable():
    rule = ExpiryDateRule()
    product = EvaluateProductRequest(
        productId="PROD-002C",
        productType="electronics",
        expiryDate=""
    )
    assert rule.is_applicable(product) is False
    res = rule.validate(product)
    assert res.status == RuleStatus.NOT_APPLICABLE


def test_expiry_unconfirmed_manual_review():
    rule = ExpiryDateRule()
    product = EvaluateProductRequest(
        productId="PROD-003",
        productType=None,
        expiryDate=None
    )
    res = rule.validate(product)
    assert res.status == RuleStatus.MANUAL_REVIEW

