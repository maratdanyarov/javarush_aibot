from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NewsItem


def is_relevant(item: NewsItem, keywords: list[str]) -> bool:
    searchable = (item.title + " " + item.summary).lower()
    return any(kw.lower() in searchable for kw in keywords)


async def is_duplicate(item: NewsItem, db: AsyncSession) -> bool:

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
