from datetime import UTC, datetime

import pytest

from app.filters import is_duplicate, is_relevant
from app.models import NewsItem


def test_is_relevant_success():
    item = NewsItem(
        title="Python is old language?", summary="Python is a modern language."
    )
    keywords = ["python", "swift", "java"]
    assert is_relevant(item, keywords) is True


def test_is_relevant_failure():
    item = NewsItem(
        title="Precise Agriculture today",
        summary="Precise Agriculture today is still relevant",
    )
    keywords = ["python", "swift", "java"]
    assert is_relevant(item, keywords) is False


@pytest.mark.asyncio
async def test_is_duplicate_false_when_empty(db_session):
    item = NewsItem(
        url="https://test.com",
        content_hash="hash1",
        title="title1",
        summary="summary1",
        published_at=datetime.now(UTC),
    )
    assert await is_duplicate(item, db_session) is False


@pytest.mark.asyncio
async def test_is_duplicate_true_when_exists(db_session):
    existing_item = NewsItem(
        url="https://test.com",
        content_hash="hash1",
        title="Existing",
        summary="Summary",
        published_at=datetime.now(UTC),
        source="Src",
    )
    db_session.add(existing_item)
    await db_session.flush()

    new_item = NewsItem(url="https://test.com", content_hash="hash1", title="New")

    assert await is_duplicate(new_item, db_session) is True


@pytest.mark.asyncio
async def test_is_duplicate_false_same_object(db_session):
    item = NewsItem(
        url="https://test.com",
        content_hash="hash1",
        title="T",
        summary="S",
        published_at=datetime.now(UTC),
        source="Src",
    )
    db_session.add(item)
    await db_session.flush()

    assert await is_duplicate(item, db_session) is False
