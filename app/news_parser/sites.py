"""RSS feed parser: fetches, parses, and persists news items from website sources."""

import asyncio
from datetime import UTC, datetime

import feedparser
import httpx
from bs4 import BeautifulSoup
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NewsItem, Source
from app.utils import is_duplicate, make_content_hash


class SiteParser:
    """Fetches news from an RSS feed URL, deduplicates items, and persists new ones."""

    async def fetch(self, source: Source, db_session: AsyncSession) -> list[NewsItem]:
        """Fetch and save new RSS items from *source*, returning the newly created NewsItems."""
        raw_news_items = await _parse_rss(source.url)
        if not raw_news_items:
            logger.info(f"No news found for {source.url}")
            return []

        news_items = []

        for item in raw_news_items:
            if not item.get("title"):
                continue

            content_hash = make_content_hash(item["title"], item.get("url", ""))
            if await is_duplicate(content_hash, db_session):
                logger.debug(f"Duplicate skipped: {item['title'][:50]}")
                continue

            news_item = NewsItem(
                title=item["title"],
                url=item.get("url"),
                summary=item.get("summary", ""),
                raw_text=item.get("raw_text"),
                source=item.get("source", source.name),
                source_id=source.id,
                published_at=item.get("published_at") or datetime.now(UTC),
                content_hash=content_hash,
            )

            db_session.add(news_item)
            await db_session.flush()
            news_items.append(news_item)

        if news_items:
            await db_session.commit()
            logger.info(f"Saved {len(news_items)} news items for {source.name}")
        else:
            logger.info(f"No news items for {source.name}")

        return news_items


async def _parse_rss(url: str) -> list[dict]:
    """RSS feed parser"""
    logger.info(f"Parsing RSS feed: {url}")

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(
                url, headers={"User-Agent": "AIBot/1.0 RSS Reader"}
            )
            response.raise_for_status()
        feed = await asyncio.to_thread(feedparser.parse, response.content)

        if not feed.entries:
            logger.warning(f"No entries in RSS feed: {url}")
            return []

        items = []
        for entry in feed.entries:
            published_at = _parse_date(entry)
            summary = ""

            summary_raw = entry.get("summary")
            if isinstance(summary_raw, str):
                summary = summary_raw
            else:
                content_raw = entry.get("content")
                if isinstance(content_raw, list) and len(content_raw) > 0:
                    first_content = content_raw[0]
                    if isinstance(first_content, dict):
                        value = first_content.get("value")
                        if isinstance(value, str):
                            summary = value

            summary = _strip_html(summary)

            title_raw = entry.get("title")
            title = title_raw.strip() if isinstance(title_raw, str) else ""

            link_raw = entry.get("link")
            item_url = link_raw if isinstance(link_raw, str) else ""

            source_raw = None
            if isinstance(feed.feed, dict):
                source_raw = feed.feed.get("title")
            source = source_raw if isinstance(source_raw, str) else url

            items.append(
                {
                    "title": title,
                    "url": item_url,
                    "summary": summary[:2000],
                    "source": source,
                    "published_at": published_at,
                    "raw_text": None,
                }
            )

        logger.info(f"RSS {url}: got {len(items)} items")
        return items

    except httpx.TimeoutException:
        logger.error(f"Timeout while fetching RSS: {url}")
        return []
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP {e.response.status_code} while fetching RSS: {url}")
        return []
    except httpx.RequestError:
        logger.error(f"Network error while fetching RSS: {url}")
        return []
    except Exception:
        logger.error(f"Unknown error while fetching RSS: {url}")
        return []


def _parse_date(entry) -> datetime:
    """Extract a timezone-aware UTC datetime from a feedparser entry, falling back to now()."""
    for field in ("published_parsed", "updated_parsed", "created_parsed"):
        value = entry.get(field)
        if value:
            try:
                return datetime(*value[:6], tzinfo=UTC)
            except Exception:
                logger.error(f"Failed to parse {field}: {value}")
                pass

    return datetime.now(UTC)


def _strip_html(text: str) -> str:
    """Strip HTML tags from *text* using BeautifulSoup and return plain text."""
    if not text:
        return ""
    return BeautifulSoup(text, "html.parser").get_text(separator="").strip()

