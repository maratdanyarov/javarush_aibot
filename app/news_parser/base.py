"""Parser protocol that every news source parser must implement."""

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NewsItem, Source


class ParserProtocol(Protocol):
    """Structural protocol that every news source parser must implement."""

    async def fetch(self, source: Source, db_session: AsyncSession) -> list[NewsItem]:
        """Fetch new items from *source*, persist them via *db_session*, and return the list."""
        ...
