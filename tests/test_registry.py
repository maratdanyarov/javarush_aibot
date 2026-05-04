import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Source, SourceType
from app.news_parser.registry import PARSERS
from app.news_parser.sites import SiteParser
from app.news_parser.telegram import TelegramParser


def test_parsers_registry_mapping():
    assert isinstance(PARSERS[SourceType.site], SiteParser)
    assert isinstance(PARSERS[SourceType.telegram], TelegramParser)

@pytest.mark.asyncio
async def test_telegram_parser_fetch_returns_empty_list(db_session: AsyncSession):
    source = Source(
        name="Test TG Channel",
        type=SourceType.telegram,
        url="https://t.me/test_channel",
    )

    parser = TelegramParser()

    result = await parser.fetch(source, db_session)

    assert isinstance(result, list)
    assert len(result) == 0
