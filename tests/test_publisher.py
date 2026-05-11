"""Unit tests for the Telegram post publisher."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from app.models import Post, PostStatus
from app.telegram.publisher import publish_post

pytestmark = pytest.mark.asyncio

async def test_publish_post_success(db_session):
    post = Post(
        news_id="test-news-id",
        generated_text="AI Generated Content",
        status=PostStatus.generated
    )
    db_session.add(post)
    await db_session.flush()

    mock_client = MagicMock()
    mock_client.send_message = AsyncMock()

    with patch("app.telegram.publisher.get_client") as mock_get_client:
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=mock_client)
        cm.__aexit__ = AsyncMock(return_value=False)
        mock_get_client.return_value = cm

        await publish_post(post, db_session)

        mock_client.send_message.assert_awaited_once()
        assert post.status == PostStatus.published
        assert post.published_at is not None

        result = await db_session.execute(select(Post).where(Post.id == post.id))
        db_post = result.scalar_one()
        assert db_post.status == PostStatus.published

async def test_publish_post_idempotency(db_session):
    post = Post(
        news_id="test-news-id",
        generated_text="Content",
        status=PostStatus.published,
        published_at=datetime.now(UTC)
    )
    db_session.add(post)
    await db_session.flush()

    with patch("app.telegram.publisher.get_client") as mock_get_client:
        await publish_post(post, db_session)
        mock_get_client.assert_not_called()

async def test_publish_post_failure(db_session):
    post = Post(
        news_id="test-news-id",
        generated_text="Content",
        status=PostStatus.generated
    )
    db_session.add(post)
    await db_session.flush()

    mock_client = MagicMock()
    mock_client.send_message = AsyncMock(side_effect=Exception("Telegram Error"))

    with patch("app.telegram.publisher.get_client") as mock_get_client:
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=mock_client)
        cm.__aexit__ = AsyncMock(return_value=False)
        mock_get_client.return_value = cm

        await publish_post(post, db_session)

        assert post.status == PostStatus.failed
        assert post.error_message == "Telegram Error"

        result = await db_session.execute(select(Post).where(Post.id == post.id))
        db_post = result.scalar_one()
        assert db_post.status == PostStatus.failed
