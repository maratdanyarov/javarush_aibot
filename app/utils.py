"""Shared utility helpers: content hashing and database-level duplicate detection."""

import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NewsItem


def make_content_hash(title: str, url: str = "") -> str:
    """
    Hash for news deduplication.
    The news items with the same title and url have the same hash.
    """
    raw = f"{title.lower().strip()}|{url.lower().strip()}"
    return hashlib.md5(raw.encode()).hexdigest()


async def is_duplicate(content_hash: str, db: AsyncSession) -> bool:
    """Return True if a NewsItem with *content_hash* already exists in the database."""
    result = await db.execute(
        select(NewsItem.id).where(NewsItem.content_hash == content_hash).limit(1)
    )
    return result.scalar() is not None
