from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NewsItem, Source


class ParserProtocol(Protocol):
    async def fetch(self, source: Source, db_session: AsyncSession) -> list[NewsItem]:
        ...
