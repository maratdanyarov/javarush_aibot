"""News item filter predicates: keyword relevance, deduplication, and language detection."""

from langdetect import LangDetectException, detect
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NewsItem


def is_relevant(item: NewsItem, keywords: list[str]) -> bool:
    """Return True if any keyword appears in the item's combined title and summary."""
    searchable = (item.title + " " + item.summary).lower()
    return any(kw.lower() in searchable for kw in keywords)


async def is_duplicate(item: NewsItem, db: AsyncSession) -> bool:
    """Return True if another NewsItem with the same URL and content_hash already exists."""

    result = await db.execute(
        select(NewsItem.id)
        .where(
            NewsItem.url == item.url,
            NewsItem.content_hash == item.content_hash,
            NewsItem.id != item.id,
        )
        .limit(1)
    )
    return result.scalar() is not None


def is_allowed_language(item: NewsItem, allowed: list[str]) -> bool:
    """Return True if the detected language is in *allowed*, or if detection is inconclusive."""
    text = item.raw_text or item.summary
    if not text or len(text) < 20:
        return True
    try:
        lang = detect(text)
        return lang in allowed
    except LangDetectException as e:
        logger.warning(f"Could not detect language for item '{item.title}': {e}")
        return True
