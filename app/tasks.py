import asyncio

from celery import chain
from loguru import logger
from sqlalchemy import select

from app.ai.generator import generate_post
from app.config import settings
from app.db import AsyncSessionLocal
from app.filters import is_allowed_language, is_duplicate, is_relevant
from app.models import Keyword, NewsItem, Post, Source
from app.news_parser.registry import PARSERS
from celery_worker import celery_app


@celery_app.task(name="app.tasks.fetch_news_task", bind=True, max_retries=3)
def fetch_news_task(self):
    logger.info("Starting scheduled fetch_news_task.")

    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Source).where(Source.enabled.is_(True)))
            sources = result.scalars().all()

            if not sources:
                logger.warning("No enabled sources found.")
                return []

            all_new_ids = []

            for source in sources:
                try:
                    parser = PARSERS.get(source.type)
                    if parser is None:
                        logger.warning(
                            f"No parser registered for '{source.type}', "
                            f"skipping '{source.name}'"
                        )
                        continue
                    saved_items = await parser.fetch(source, db)
                    all_new_ids.extend(item.id for item in saved_items)
                    logger.info(
                        f"Source '{source.name}': saved {len(saved_items)} news items."
                    )
                except Exception as e:
                    logger.error(f"Failed to fetch source '{source.name}': {e}")

            logger.info(f"fetch_news_task done. Saved {len(all_new_ids)} news items.")

            chain(
                filter_task.s(all_new_ids), generate_task.s(), publish_task.s()
            ).delay()
            return all_new_ids

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error(f"Failed to run fetch_news_task: {e}")
        raise self.retry(exc=e, countdown=60) from e


@celery_app.task(name="app.tasks.filter_task", bind=True, max_retries=3)
def filter_task(self, news_item_ids: list[str]):
    logger.info("Starting filter_task.")

    async def _run():
        async with AsyncSessionLocal() as db:
            kw_result = await db.execute(
                select(Keyword).where(Keyword.enabled.is_(True))
            )
            keywords = [kw.word for kw in kw_result.scalars().all()]
            filtered_results = []
            for news_item_id in news_item_ids:
                item = await db.get(NewsItem, news_item_id)
                if item is None:
                    continue
                if (
                    not await is_duplicate(item, db)
                    and is_relevant(item, keywords)
                    and is_allowed_language(item, settings.allowed_languages)
                ):
                    filtered_results.append(news_item_id)

        return filtered_results

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error(f"Failed to run filter_task: {e}")
        raise self.retry(exc=e, countdown=60) from e


@celery_app.task(name="app.tasks.generate_task", bind=True, max_retries=3)
def generate_task(self, news_item_ids: list[str]):
    logger.info("Starting generate_task.")

    async def _run():
        generated_posts_ids = []
        async with AsyncSessionLocal() as db:
            for news_item_id in news_item_ids:
                item = await db.get(NewsItem, news_item_id)
                if item is None:
                    continue
                generated_text = await generate_post(item)
                new_post = Post(
                    news_item_id=news_item_id,
                    generated_text=generated_text,
                    status="generated",
                )
                db.add(new_post)
                await db.flush()
                generated_posts_ids.append(new_post.id)
            await db.commit()

        return generated_posts_ids

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error(f"Failed to run generate_task: {e}")
        raise self.retry(exc=e, countdown=60) from e


@celery_app.task(name="app.tasks.publish_task", bind=True, max_retries=3)
def publish_task(news_item_ids: list[str]):
    logger.info("Starting publish_task.")
    return
