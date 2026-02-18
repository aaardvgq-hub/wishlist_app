"""Schemas for reservation — no contributor identity exposed to owner."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReserveResponse(BaseModel):
    """Response after reserving an item. Owner must not see session_id."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_id: UUID
    created_at: datetime
    cancelled_at: datetime | None = None


class ReservationPublicView(BaseModel):
    """Reservation as shown to anyone (including owner). No anonymous_session_id."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_id: UUID
    created_at: datetime
    cancelled_at: datetime | None = None
