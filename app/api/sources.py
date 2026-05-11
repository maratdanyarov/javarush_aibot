"""CRUD endpoints for managing news sources (RSS feeds and Telegram channels)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.schemas import SourceCreate, SourceRead, SourceUpdate
from app.db import get_db
from app.models import Source

router = APIRouter(tags=["Sources"])


@router.get(
    "/sources", response_model=list[SourceRead], summary="List all news sources"
)
async def list_sources(db: AsyncSession = Depends(get_db)):
    """Return all sources ordered by creation date descending."""
    result = await db.execute(select(Source).order_by(Source.created_at.desc()))
    return result.scalars().all()


@router.get(
    "/sources/{source_id}", response_model=SourceRead, summary="Get source by ID"
)
async def get_source(source_id: str, db: AsyncSession = Depends(get_db)):
    """Return a single source by its UUID, or 404 if not found."""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.post(
    "/sources",
    response_model=SourceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create new news source",
)
async def create_source(payload: SourceCreate, db: AsyncSession = Depends(get_db)):
    """Create and persist a new news source, returning the saved record."""
    source = Source(**payload.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


@router.patch(
    "/sources/{source_id}", response_model=SourceRead, summary="Update news source"
)
async def update_source(
    source_id: str, payload: SourceUpdate, db: AsyncSession = Depends(get_db)
):
    """Partially update a source's fields, returning the updated record."""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(source, key, value)

    await db.commit()
    await db.refresh(source)

    return source


@router.delete(
    "/sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete news source",
)
async def delete_source(source_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a source by its UUID and return 204 No Content."""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    await db.delete(source)
    await db.commit()
    return None
