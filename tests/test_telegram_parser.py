"""Tests for the Telegram channel parser: successful fetch and duplicate-skipping."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from app.models import NewsItem, Source, SourceType
from app.news_parser.telegram import TelegramParser
from app.utils import make_content_hash

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_message():
    message = MagicMock()
    message.id = 123
    message.text = "Hello Telegram\nThis is a test message."
    message.date = datetime.now(UTC)
    return message


async def test_telegram_parser_fetch_success(db_session, mock_message):
    source = Source(
        id="tg-source-id",
        name="Test Channel",
        url="https://t.me/test_channel",
        type=SourceType.telegram,
    )
    db_session.add(source)
    await db_session.flush()

    mock_client = MagicMock()

    async def mock_iter_messages(*args, **kwargs):
        yield mock_message

    mock_client.iter_messages.side_effect = mock_iter_messages

    with patch("app.news_parser.telegram.get_client") as mock_get_client:
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=mock_client)
        cm.__aexit__ = AsyncMock()
        mock_get_client.return_value = cm

        parser = TelegramParser(limit=5)
        news_items = await parser.fetch(source, db_session)

        assert len(news_items) == 1
        assert news_items[0].title == "Hello Telegram"
        assert news_items[0].source_id == source.id

        result = await db_session.execute(
            select(NewsItem).where(NewsItem.source_id == source.id)
        )
        items = result.scalars().all()
        assert len(items) == 1


async def test_telegram_parser_duplicate_skipping(db_session, mock_message):
    source = Source(
        id="tg-source-2",
        name="Channel 2",
        url="https://t.me/chan2",
        type=SourceType.telegram,
    )
    db_session.add(source)

    title = "Hello Telegram"
    unique_id = f"{source.url}_{mock_message.id}"
    h = make_content_hash(title, unique_id)

    existing = NewsItem(
        title=title,
        summary="old",
        raw_text="old",
        source=source.name,
        source_id=source.id,
        published_at=datetime.now(UTC),
        content_hash=h,
    )
    db_session.add(existing)
    await db_session.flush()

    mock_client = MagicMock()

    async def mock_iter_messages(*args, **kwargs):
        yield mock_message

    mock_client.iter_messages.side_effect = mock_iter_messages

    with patch("app.news_parser.telegram.get_client") as mock_get_client:
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=mock_client)
        cm.__aexit__ = AsyncMock()
        mock_get_client.return_value = cm

        parser = TelegramParser()
        news_items = await parser.fetch(source, db_session)

        assert len(news_items) == 0
