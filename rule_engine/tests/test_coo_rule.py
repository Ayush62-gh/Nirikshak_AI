"""
Unit tests for LM-RULE-COO-009: Country of Origin Declaration Rule.
"""

from app.models.product import EvaluateProductRequest
from app.models.rule_result import RuleStatus
from app.rules.country_of_origin_rule import CountryOfOriginRule


def test_coo_imported_pass():
    rule = CountryOfOriginRule()
    product = EvaluateProductRequest(
        productId="PROD-001",
        isImported=True,
        countryOfOrigin="India"
    )
    res = rule.validate(product)
    assert res.status == RuleStatus.PASS
    assert "Country of Origin declaration is present" in res.message


def test_coo_imported_missing_fail():
    rule = CountryOfOriginRule()
    product = EvaluateProductRequest(
        productId="PROD-002",
        isImported=True,
        countryOfOrigin=None
    )
    res = rule.validate(product)
    assert res.status == RuleStatus.FAIL
    assert "Mandatory Country of Origin declaration is missing" in res.message


def test_coo_unconfirmed_manual_review():
    rule = CountryOfOriginRule()
    product = EvaluateProductRequest(
        productId="PROD-003",
        isImported=None,
        countryOfOrigin=None
    )
    res = rule.validate(product)
    assert res.status == RuleStatus.MANUAL_REVIEW


def test_coo_domestic_not_applicable():
    rule = CountryOfOriginRule()
    product = EvaluateProductRequest(
        productId="PROD-004",
        isImported=False,
        countryOfOrigin=None
    )
    assert rule.is_applicable(product) is False
