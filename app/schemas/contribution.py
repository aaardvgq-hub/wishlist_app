"""Schemas for contribution — no contributor identity exposed to owner."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ContributeRequest(BaseModel):
    """Payload for contributing to an item."""

    amount: Decimal = Field(..., gt=0, description="Contribution amount (must be > 0)")


class ContributeResponse(BaseModel):
    """Response after contributing. Only totals/progress, no identities."""

    item_id: UUID
    contributed_total: Decimal
    target_price: Decimal
    progress_percent: float
    amount_added: Decimal
