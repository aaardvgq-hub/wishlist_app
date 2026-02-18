"""Money handling: Decimal-only, no float math. Safe sum and progress percent."""

from decimal import Decimal


def safe_sum(*values: Decimal) -> Decimal:
    """Sum of Decimal values; returns Decimal('0') if no values. Safe for money."""
    if not values:
        return Decimal("0")
    total = Decimal("0")
    for v in values:
        total += Decimal(str(v))
    return total


def progress_percent(contributed: Decimal, target: Decimal) -> Decimal:
    """
    Contribution progress as 0--100. Returns min(contributed/target*100, 100).
    Returns Decimal('0') if target <= 0.
    """
    if target <= 0:
        return Decimal("0")
    pct = (contributed / target) * 100
    return min(pct, Decimal("100"))
