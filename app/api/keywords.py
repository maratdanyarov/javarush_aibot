"""CRUD endpoints for managing keyword filters used during news relevance screening."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.schemas import KeywordCreate, KeywordRead, KeywordUpdate
from app.db import get_db
from app.models import Keyword

router = APIRouter(tags=["Keywords"])


@router.get("/keywords", response_model=list[KeywordRead], summary="List all keywords")
async def get_keywords(db: AsyncSession = Depends(get_db)):
    """Return all keywords ordered by ID."""
    result = await db.execute(select(Keyword).order_by(Keyword.id))
    return result.scalars().all()


@router.get(
    "/keywords/{keyword_id}", response_model=KeywordRead, summary="Get keyword by ID"
)
async def get_keyword(keyword_id: str, db: AsyncSession = Depends(get_db)):
    """Return a single keyword by its UUID, or 404 if not found."""
    keyword = await db.get(Keyword, keyword_id)
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Keyword not found"
        )
    return keyword


@router.post(
    "/keywords",
    response_model=KeywordRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create new keyword",
)
async def create_keyword(payload: KeywordCreate, db: AsyncSession = Depends(get_db)):
    """Create and persist a new keyword, returning the saved record."""
    keyword = Keyword(**payload.model_dump())
    db.add(keyword)
    await db.commit()
    await db.refresh(keyword)
    return keyword


@router.put(
    "/keywords/{keyword_id}", response_model=KeywordRead, summary="Update keyword"
)
async def update_keyword(
    keyword_id: str, payload: KeywordUpdate, db: AsyncSession = Depends(get_db)
):
    """Partially update a keyword's fields, returning the updated record."""
    keyword = await db.get(Keyword, keyword_id)
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Keyword not found"
        )
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(keyword, key, value)

    await db.commit()
    await db.refresh(keyword)

    return keyword


@router.delete(
    "/keywords/{keyword_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete keyword",
)
async def delete_keyword(keyword_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a keyword by its UUID and return 204 No Content."""
    keyword = await db.get(Keyword, keyword_id)
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Keyword not found"
        )
    await db.delete(keyword)
    await db.commit()
    return None
