"""Publishes AI-generated posts to the configured Telegram channel via Telethon."""

from datetime import UTC, datetime

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Post, PostStatus
from app.telegram.client import get_client


async def publish_post(post: Post, db: AsyncSession) -> None:
    """Send *post* to the configured Telegram channel and update its status to published or failed."""
    if post.status == PostStatus.published:
        logger.info(f"Post {post.id} already published. Skipping.")
        return

    async with get_client() as client:
        try:
            logger.info(f"Publishing post {post.id} to {settings.tg_channel}")
            await client.send_message(settings.tg_channel, post.generated_text)

            post.status = PostStatus.published
            post.published_at = datetime.now(UTC)
            await db.commit()
            logger.info(f"Successfully published post {post.id}")

        except Exception as e:
            logger.error(f"Failed to publish post {post.id}: {e}")
            post.status = PostStatus.failed
            post.error_message = str(e)
            await db.commit()
