from app.models import SourceType
from app.news_parser.registry import PARSERS
from app.news_parser.sites import SiteParser
from app.news_parser.telegram import TelegramParser


def test_parsers_registry_mapping():
    assert isinstance(PARSERS[SourceType.site], SiteParser)
    assert isinstance(PARSERS[SourceType.telegram], TelegramParser)
