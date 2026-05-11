"""Telegram channel parser: fetches recent messages via the Telethon MTProto client."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NewsItem, Source
from app.telegram.client import get_client
from app.utils import is_duplicate, make_content_hash


class TelegramParser:
    """Fetches recent messages from a Telegram channel via the Telethon MTProto client."""

    def __init__(self, limit: int = 20):
        """Configure the parser to fetch at most *limit* recent messages per channel."""
        self.limit = limit

    async def fetch(self, source: Source, db_session: AsyncSession) -> list[NewsItem]:
        """Fetch recent messages from a Telegram channel, skip duplicates, and persist new items."""
        async with get_client() as client:
            news_items = []
            channel_name = source.url.rstrip("/").split("/")[-1]

            async for message in client.iter_messages(channel_name, limit=self.limit):
                if not message.text:
                    continue

                title = message.text.split("\n")[0][:100]

                unique_id = f"{source.url}_{message.id}"
                content_hash = make_content_hash(title, unique_id)

                if await is_duplicate(content_hash, db_session):
                    continue

                news_item = NewsItem(
                    title=title,
                    summary=message.text[:500],
                    raw_text=message.text,
                    source=source.name,
                    source_id=source.id,
                    published_at=message.date,
                    content_hash=content_hash,
                )

                db_session.add(news_item)
                news_items.append(news_item)

        if news_items:
            await db_session.commit()

        return news_items
