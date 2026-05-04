from app.models import SourceType
from app.news_parser.base import ParserProtocol
from app.news_parser.sites import SiteParser
from app.news_parser.telegram import TelegramParser

PARSERS: dict[SourceType, ParserProtocol] = {
    SourceType.site: SiteParser(),
    SourceType.telegram: TelegramParser(),
}