"""Partial unique index: one active reservation per item (prevents race double-reserve).

Why DB unique index is sufficient (no app-level locking):
- Two concurrent requests can both pass the "no active reservation" check and attempt INSERT.
- The partial unique index on (item_id) WHERE cancelled_at IS NULL allows only one such row per item.
- The second INSERT raises IntegrityError; the app catches it, rolls back, and returns 409.
- Transaction boundary: get_db yields a session and commits after the request handler returns,
  so reserve() runs inside one transaction; the index is enforced at commit/flush time.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_reservations_item_id_active",
        "reservations",
        ["item_id"],
        unique=True,
        postgresql_where=sa.text("cancelled_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_reservations_item_id_active", table_name="reservations")
