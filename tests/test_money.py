"""Unit tests for money helpers (Decimal-only, no float math)."""

from decimal import Decimal

import pytest

from app.core.money import progress_percent, safe_sum


def test_safe_sum_empty() -> None:
    assert safe_sum() == Decimal("0")


def test_safe_sum_single() -> None:
    assert safe_sum(Decimal("10.50")) == Decimal("10.50")


def test_safe_sum_multiple() -> None:
    assert safe_sum(Decimal("1.01"), Decimal("2.02"), Decimal("3.03")) == Decimal("6.06")


def test_progress_percent_zero_target() -> None:
    assert progress_percent(Decimal("50"), Decimal("0")) == Decimal("0")


def test_progress_percent_half() -> None:
    assert progress_percent(Decimal("50"), Decimal("100")) == Decimal("50")


def test_progress_percent_capped_at_100() -> None:
    assert progress_percent(Decimal("150"), Decimal("100")) == Decimal("100")
