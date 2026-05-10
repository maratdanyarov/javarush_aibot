import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC
from sqlalchemy import select

from app.models import Source, Keyword, NewsItem, Post, PostStatus, SourceType
from app.news_parser.sites import SiteParser
from app.ai.generator import generate_post
from app.telegram.publisher import publish_post
from app.filters import is_relevant, is_duplicate, is_allowed_language
from app.config import settings

pytestmark = pytest.mark.asyncio

async def test_full_pipeline_flow(db_session):
    source = Source(
        name="Test News Site",
        url="https://example.com/rss",
        type=SourceType.site,
        enabled=True
    )
    keyword = Keyword(word="python", enabled=True)
    db_session.add(source)
    db_session.add(keyword)
    await db_session.commit()

    mock_rss_xml = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Python is great</title>
      <link>https://example.com/1</link>
      <description>A summary about Python programming</description>
    </item>
  </channel>
</rss>"""

    mock_httpx_client = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = mock_rss_xml.encode("utf-8")
    mock_resp.raise_for_status = MagicMock()
    mock_httpx_client.get.return_value = mock_resp

    mock_tg_client = AsyncMock()
    mock_tg_client.send_message = AsyncMock()

    with patch("app.news_parser.sites.httpx.AsyncClient") as mock_httpx_class, \
         patch("app.ai.generator.generate_text", new_callable=AsyncMock) as mock_gen_text, \
         patch("app.telegram.publisher.get_client") as mock_get_client, \
         patch("app.filters.detect") as mock_detect:
        
        mock_httpx_class.return_value.__aenter__.return_value = mock_httpx_client
        mock_gen_text.return_value = "AI Post: Python is awesome! 🐍"
        
        cm_tg = MagicMock()
        cm_tg.__aenter__ = AsyncMock(return_value=mock_tg_client)
        cm_tg.__aexit__ = AsyncMock(return_value=False)
        mock_get_client.return_value = cm_tg
        
        mock_detect.return_value = "en"

        parser = SiteParser()
        new_items = await parser.fetch(source, db_session)
        assert len(new_items) == 1
        item = new_items[0]
        assert item.title == "Python is great"

        kw_result = await db_session.execute(select(Keyword).where(Keyword.enabled.is_(True)))
        keywords = [k.word for k in kw_result.scalars().all()]
        
        assert is_relevant(item, keywords) is True
        assert await is_duplicate(item, db_session) is False
        assert is_allowed_language(item, settings.allowed_languages) is True

        generated_text = await generate_post(item)
        mock_gen_text.assert_awaited_once()
        assert generated_text == "AI Post: Python is awesome! 🐍"
        
        post = Post(
            news_id=item.id,
            generated_text=generated_text,
            status=PostStatus.generated
        )
        db_session.add(post)
        await db_session.commit()

        await publish_post(post, db_session)

        mock_tg_client.send_message.assert_awaited_once_with(
            settings.tg_channel,
            "AI Post: Python is awesome! 🐍"
        )
        
        res_item = await db_session.execute(select(NewsItem).where(NewsItem.id == item.id))
        assert res_item.scalar_one() is not None
        
        res_post = await db_session.execute(select(Post).where(Post.id == post.id))
        db_post = res_post.scalar_one()
        assert db_post.status == PostStatus.published
        assert db_post.published_at is not None
