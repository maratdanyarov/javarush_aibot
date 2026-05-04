from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from app.models import NewsItem, Source, SourceType
from app.news_parser.sites import fetch_from_site
from app.utils import make_content_hash

pytestmark = pytest.mark.asyncio


async def test_fetch_from_site_success(db_session):
    source = Source(
        id="test-source-id",
        name="Test Source",
        url="https://test.com/rss",
        type=SourceType.site,
        enabled=True,
    )
    db_session.add(source)

    await db_session.flush()

    mock_rss_content = b"""<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
    <channel>
        <title>Test Feed</title>
        <item>
            <title>Test News Title</title>
            <link>https://test.com/news/1</link>
            <description>Test Summary</description>
            <pubDate>Wed, 01 May 2024 10:00:00 +0000</pubDate>
        </item>
    </channel>
    </rss>"""

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = mock_rss_content
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        news_items = await fetch_from_site(source, db_session)
        # Assert: Check return value
        assert len(news_items) == 1
        assert news_items[0].title == "Test News Title"
        assert news_items[0].url == "https://test.com/news/1"

        result = await db_session.execute(
            select(NewsItem).where(NewsItem.source_id == source.id)
        )
        db_items = result.scalars().all()
        assert len(db_items) == 1
        assert db_items[0].title == "Test News Title"


async def test_fetch_from_site_duplicate_skipping(db_session):

    source = Source(
        id="source-2",
        name="Source 2",
        url="https://test2.com/rss",
        type=SourceType.site,
    )
    db_session.add(source)

    title = "Duplicate Title"
    url = "https://test2.com/1"
    existing_item = NewsItem(
        title=title,
        url=url,
        summary="Old content",
        source="Source 2",
        source_id=source.id,
        published_at=datetime.now(UTC),
        content_hash=make_content_hash(title, url),
    )
    db_session.add(existing_item)
    await db_session.flush()

    #
    mock_rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
    <channel>
        <item>
            <title>{title}</title>
            <link>{url}</link>
            <description>New content in RSS</description>
        </item>
    </channel>
    </rss>""".encode()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = mock_rss_content
        mock_get.return_value = mock_resp

        news_items = await fetch_from_site(source, db_session)

        assert len(news_items) == 0
