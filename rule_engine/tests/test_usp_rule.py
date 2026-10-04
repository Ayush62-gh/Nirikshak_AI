"""
Unit tests for LM-RULE-USP-010: Unit Sale Price Declaration Rule.
"""

from app.models.product import EvaluateProductRequest
from app.models.rule_result import RuleStatus
from app.rules.unit_sale_price_rule import UnitSalePriceRule


def test_usp_pass_field():
    rule = UnitSalePriceRule()
    product = EvaluateProductRequest(
        productId="PROD-001",
        netQuantity="500 g",
        mrp="Rs. 100",
        unitSalePrice="Rs 0.20/g"
    )
    assert rule.is_applicable(product) is True
    res = rule.validate(product)
    assert res.status == RuleStatus.PASS


def test_usp_pass_in_mrp_snippet():
    rule = UnitSalePriceRule()
    product = EvaluateProductRequest(
        productId="PROD-002",
        netQuantity="200 g",
        mrp="Rs. 50 (Rs 0.25/g) incl. of all taxes"
    )
    assert rule.is_applicable(product) is True
    res = rule.validate(product)
    assert res.status == RuleStatus.PASS


def test_usp_unverified_manual_review():
    rule = UnitSalePriceRule()
    product = EvaluateProductRequest(
        productId="PROD-003",
        netQuantity="500 g",
        mrp="Rs. 100",
        unitSalePrice="invalid_price"
    )
    assert rule.is_applicable(product) is True
    res = rule.validate(product)
    assert res.status == RuleStatus.MANUAL_REVIEW


def test_usp_missing_with_net_quantity_manual_review():
    rule = UnitSalePriceRule()
    product = EvaluateProductRequest(
        productId="PROD-004",
        netQuantity="500 g",
        mrp="Rs. 100",
        unitSalePrice=None
    )
    assert rule.is_applicable(product) is True
    res = rule.validate(product)
    assert res.status == RuleStatus.MANUAL_REVIEW


def test_usp_not_provided_no_net_quantity_not_applicable():
    rule = UnitSalePriceRule()
    product = EvaluateProductRequest(
        productId="PROD-005",
        netQuantity=None,
        mrp="Rs. 100",
        unitSalePrice=None
    )
    assert rule.is_applicable(product) is False

