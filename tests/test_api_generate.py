import pytest
from unittest.mock import patch, AsyncMock
from starlette import status
from datetime import datetime, UTC
from app.models import NewsItem, Post

pytestmark = pytest.mark.asyncio

async def test_manual_generate_success(client, db_session):
    # 1. Setup: Create a NewsItem in the database
    news_item = NewsItem(
        title="Test News Title",
        summary="Test News Summary",
        source="Test Source",
        published_at=datetime.now(UTC)
    )
    db_session.add(news_item)
    await db_session.flush()
    await db_session.commit()

    # 2. Mock generate_post
    with patch("app.api.generate.generate_post", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "AI Generated Content"
        
        # 3. Act: Call the API
        payload = {"news_item_id": news_item.id}
        response = await client.post("/api/generate", json=payload)
        
        # 4. Assert response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["generated_text"] == "AI Generated Content"
        assert data["news_id"] == news_item.id
        assert data["status"] == "generated"
        
        # 5. Assert database state
        from sqlalchemy import select
        result = await db_session.execute(select(Post).where(Post.news_id == news_item.id))
        post = result.scalar_one()
        assert post.generated_text == "AI Generated Content"

async def test_manual_generate_404(client):
    # Act: Call with non-existing ID
    payload = {"news_item_id": "non-existing-uuid"}
    response = await client.post("/api/generate", json=payload)
    
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "News item not found"

async def test_manual_generate_ai_failure(client, db_session):
    # 1. Setup
    news_item = NewsItem(
        title="Test", summary="S", source="Src", published_at=datetime.now(UTC)
    )
    db_session.add(news_item)
    await db_session.flush()
    await db_session.commit()
    
    # 2. Mock AI failure
    with patch("app.api.generate.generate_post", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = Exception("OpenAI down")
        
        # 3. Act
        payload = {"news_item_id": news_item.id}
        response = await client.post("/api/generate", json=payload)
        
        # 4. Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"] == "AI generation failed."
