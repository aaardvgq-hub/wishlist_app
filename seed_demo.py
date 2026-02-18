#!/usr/bin/env python3
"""
Demo seed script: creates demo user, wishlist, items, and sample contributions.
Prints the public share URL. Run after migrations: alembic upgrade head.
Usage: python seed_demo.py
"""
import asyncio
import os
import sys
from decimal import Decimal
from uuid import uuid4

# Add project root so app is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.models.contribution import Contribution
from app.models.user import User
from app.models.wish_item import WishItem
from app.models.wishlist import Wishlist


DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo-password-123"
DEMO_TITLE = "My Birthday Wishlist"
BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:3000")


async def main() -> None:
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/wishlist",
    )
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == DEMO_EMAIL))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                email=DEMO_EMAIL,
                hashed_password=hash_password(DEMO_PASSWORD),
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)
            print(f"Created demo user: {user.email} (id={user.id})")
        else:
            print(f"Using existing demo user: {user.email}")

        result = await session.execute(
            select(Wishlist).where(Wishlist.owner_id == user.id).limit(1)
        )
        wishlist = result.scalar_one_or_none()
        if not wishlist:
            wishlist = Wishlist(
                owner_id=user.id,
                title=DEMO_TITLE,
                description="Demo list for testing reserve and contribute.",
                is_public=True,
            )
            session.add(wishlist)
            await session.flush()
            await session.refresh(wishlist)
            print(f"Created wishlist: {wishlist.title} (share_token={wishlist.share_token})")
        else:
            print(f"Using existing wishlist: {wishlist.title} (share_token={wishlist.share_token})")

        result = await session.execute(
            select(WishItem).where(WishItem.wishlist_id == wishlist.id, WishItem.is_deleted.is_(False))
        )
        items = list(result.scalars().all())
        if len(items) < 3:
            for title, target, allow in [
                ("Wireless headphones", "89.99", True),
                ("Book: Clean Code", "35.00", False),
                ("Coffee maker", "120.00", True),
            ]:
                item = WishItem(
                    wishlist_id=wishlist.id,
                    title=title,
                    target_price=Decimal(target),
                    allow_group_contribution=allow,
                )
                session.add(item)
                await session.flush()
                await session.refresh(item)
                items.append(item)
            print("Added 3 demo items.")
        else:
            print(f"Wishlist already has {len(items)} items.")

        # Add sample contributions to first item that allows group contribution
        contrib_item = next((i for i in items if i.allow_group_contribution), None)
        if contrib_item:
            result = await session.execute(
                select(Contribution).where(Contribution.item_id == contrib_item.id)
            )
            existing = result.scalars().all()
            if len(existing) < 2:
                for amount in [Decimal("20.00"), Decimal("15.50")]:
                    c = Contribution(
                        item_id=contrib_item.id,
                        anonymous_session_id=str(uuid4()),
                        amount=amount,
                    )
                    session.add(c)
                await session.flush()
                print(f"Added sample contributions to item: {contrib_item.title}")

        await session.commit()

    share_url = f"{BASE_URL}/public/{wishlist.share_token}"
    print("\n--- Demo ready ---")
    print(f"Public share URL: {share_url}")
    print(f"Login (owner):   {DEMO_EMAIL} / {DEMO_PASSWORD}")
    print("------------------\n")


if __name__ == "__main__":
    asyncio.run(main())
