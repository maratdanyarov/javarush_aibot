"""Integration tests for the posts read-only API endpoints."""

from datetime import UTC, datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.models import NewsItem, Post, PostStatus

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def sample_news(db_session: AsyncSession):
    news = NewsItem(
        id="1",
        title="Breaking News",
        summary="Some summary",
        source="Some source",
        published_at=datetime(2021, 1, 10, tzinfo=UTC),
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)
    return news


@pytest_asyncio.fixture
async def sample_post(db_session: AsyncSession, sample_news):
    post = Post(
        news_id=sample_news.id,
        generated_text="Some generated text",
        status=PostStatus.new,
        published_at=datetime(2021, 1, 10, tzinfo=UTC),
    )
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)
    return post


async def test_get_post(client, sample_post):
    response = await client.get(f"/posts/{sample_post.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == sample_post.id
    assert data["generated_text"] == "Some generated text"


async def test_get_post_not_found(client):
    response = await client.get("/posts/non-existing-post")
    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_list_posts_empty(client):
    response = await client.get("/posts")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_list_posts_filter_status(client, db_session: AsyncSession, sample_news):
    db_session.add(
        Post(
            news_id=sample_news.id,
            generated_text="New post",
            status=PostStatus.new,
            published_at=datetime(2022, 1, 1, tzinfo=UTC),
        )
    )
    db_session.add(
        Post(
            news_id=sample_news.id,
            generated_text="Published post",
            status=PostStatus.published,
            published_at=datetime(2022, 1, 2, tzinfo=UTC),
        )
    )
    await db_session.commit()

    response = await client.get("/posts?status=published")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert len(data) == 1
    assert data[0]["status"] == "published"
    assert data[0]["generated_text"] == "Published post"


async def test_list_posts_pagination(client, db_session: AsyncSession, sample_news):
    for i in range(3):
        db_session.add(Post(
            news_id=sample_news.id,
            generated_text=f"Generated text {i}",
            status=PostStatus.new,
            published_at=datetime(2022, 2, 11, tzinfo=UTC),
        ))
    await db_session.commit()

    response_limit = await client.get("/posts?limit=2")
    assert response_limit.status_code == status.HTTP_200_OK
    assert len(response_limit.json()) == 2

    response_skip = await client.get("/posts?skip=2")
    assert response_skip.status_code == status.HTTP_200_OK
    assert len(response_skip.json()) == 1
