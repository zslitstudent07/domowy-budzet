
from decimal import Decimal

from app import calculate_total


def test_sum_of_expenses():
    amounts = [
        Decimal("12.50"),
        Decimal("7.25"),
        Decimal("10.00"),
    ]
    assert calculate_total(amounts) == Decimal("29.75")


def test_empty_expenses():
    assert calculate_total([]) == Decimal("0.00")


def test_decimal_precision():
    amounts = [Decimal("0.10"), Decimal("0.20")]
    assert calculate_total(amounts) == Decimal("0.30")


def test_single_expense():
    assert calculate_total([Decimal("99.99")]) == Decimal("99.99")
