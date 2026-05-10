from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.generator import generate_post
from app.api.schemas import GenerateRequest, PostRead
from app.db import get_db
from app.models import NewsItem, Post

router = APIRouter()


@router.post("/api/generate", response_model=PostRead)
async def manual_generate(body: GenerateRequest, db: AsyncSession = Depends(get_db)):
    item = await db.get(NewsItem, body.news_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="News item not found")

    try:
        generated_text = await generate_post(item)
    except Exception as e:
        raise HTTPException(status_code=500, detail="AI generation failed.") from e

    post = Post(news_id=item.id, generated_text=generated_text, status="generated")
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post
