"""Read-only endpoints for browsing generated and published posts."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.schemas import PostRead
from app.db import get_db
from app.models import Post, PostStatus

router = APIRouter(tags=["Posts"])


@router.get(
    "/posts",
    response_model=list[PostRead],
    summary="List all posts with optional status filter",
)
async def list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: PostStatus | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    """Return a paginated list of posts ordered by creation date, optionally filtered by status."""
    query = select(Post).order_by(Post.created_at.desc())
    if status_filter is not None:
        query = query.where(Post.status == status_filter)

    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/posts/{post_id}", response_model=PostRead, summary="Get post by ID")
async def get_post(post_id: str, db: AsyncSession = Depends(get_db)):
    """Return a single post by its UUID, or 404 if not found."""
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return post
