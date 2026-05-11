"""Tests for news item filter predicates: relevance, deduplication, and language checks."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from langdetect import LangDetectException

from app.filters import is_allowed_language, is_duplicate, is_relevant
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


def test_is_allowed_language_match():
    item = NewsItem(
        title="Title",
        summary="This is a long enough text to trigger detection",
        raw_text="This is a long enough English sentence",
    )
    with patch("app.filters.detect") as mock_detect:
        mock_detect.return_value = "en"
        assert is_allowed_language(item, ["en", "ru"]) is True


def test_is_allowed_language_not_match():
    item = NewsItem(
        title="Title", summary="Some text", raw_text="Ceci est un texte français"
    )
    with patch("app.filters.detect") as mock_detect:
        mock_detect.return_value = "fr"
        assert is_allowed_language(item, ["en", "ru"]) is False


def test_is_allowed_language_exception_returns_true():
    item = NewsItem(title="Title", summary="Text", raw_text="!!! " * 8)
    with patch("app.filters.detect") as mock_detect:
        mock_detect.side_effect = LangDetectException(0, "No features in text")
        assert is_allowed_language(item, ["en"]) is True
