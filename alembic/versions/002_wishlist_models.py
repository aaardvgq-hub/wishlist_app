"""Wishlist, WishItem, Reservation, Contribution; User.is_active

Revision ID: 002
Revises: 001
Create Date: 2025-02-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"))
    op.create_table(
        "wishlists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_date", sa.Date(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("share_token", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_wishlists_owner_id", "wishlists", ["owner_id"], unique=False)
    op.create_index("ix_wishlists_share_token", "wishlists", ["share_token"], unique=True)
    op.create_table(
        "wish_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("wishlist_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wishlists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("product_url", sa.String(2048), nullable=True),
        sa.Column("image_url", sa.String(2048), nullable=True),
        sa.Column("target_price", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("allow_group_contribution", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_wish_items_wishlist_id", "wish_items", ["wishlist_id"], unique=False)
    op.create_index("ix_wish_items_is_deleted", "wish_items", ["is_deleted"], unique=False)
    op.create_table(
        "reservations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wish_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("anonymous_session_id", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_reservations_item_id", "reservations", ["item_id"], unique=False)
    op.create_index("ix_reservations_anonymous_session_id", "reservations", ["anonymous_session_id"], unique=False)
    op.create_table(
        "contributions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wish_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("anonymous_session_id", sa.String(255), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_contributions_item_id", "contributions", ["item_id"], unique=False)
    op.create_index("ix_contributions_anonymous_session_id", "contributions", ["anonymous_session_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_contributions_anonymous_session_id", table_name="contributions")
    op.drop_index("ix_contributions_item_id", table_name="contributions")
    op.drop_table("contributions")
    op.drop_index("ix_reservations_anonymous_session_id", table_name="reservations")
    op.drop_index("ix_reservations_item_id", table_name="reservations")
    op.drop_table("reservations")
    op.drop_index("ix_wish_items_is_deleted", table_name="wish_items")
    op.drop_index("ix_wish_items_wishlist_id", table_name="wish_items")
    op.drop_table("wish_items")
    op.drop_index("ix_wishlists_share_token", table_name="wishlists")
    op.drop_index("ix_wishlists_owner_id", table_name="wishlists")
    op.drop_table("wishlists")
    op.drop_column("users", "is_active")
