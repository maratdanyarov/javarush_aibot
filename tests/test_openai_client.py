"""Unit tests for the OpenAI client wrapper, including retry and error-handling behavior."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import APIStatusError, RateLimitError

from app.ai.openai_client import AIGenerationError, generate_text

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_openai_response():
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="Generated AI Text"))]
    return mock_resp


async def test_generate_text(mock_openai_response):
    with patch("app.ai.openai_client.get_ai_client") as mock_get:
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_get.return_value = mock_client

        result = await generate_text("Test prompt")

        assert result == "Generated AI Text"
        assert mock_client.chat.completions.create.await_count == 1


async def test_generate_text_retry_then_success(mock_openai_response):
    with patch("app.ai.openai_client.get_ai_client") as mock_get:
        with patch("app.ai.openai_client.asyncio.sleep", AsyncMock()):
            mock_client = AsyncMock()

            mock_client.chat.completions.create.side_effect = [
                RateLimitError(
                    message="Rate limit hit",
                    response=MagicMock(status_code=429),
                    body={},
                ),
                mock_openai_response,
            ]
            mock_get.return_value = mock_client

            result = await generate_text("Test prompt")

            assert result == "Generated AI Text"
            assert mock_client.chat.completions.create.await_count == 2


async def test_generate_text_exhaust_retries():
    with patch("app.ai.openai_client.get_ai_client") as mock_get:
        with patch("app.ai.openai_client.asyncio.sleep", AsyncMock()):
            mock_client = AsyncMock()

            mock_error = APIStatusError(
                message="Server Error", response=MagicMock(status_code=500), body={}
            )
            mock_client.chat.completions.create.side_effect = mock_error
            mock_get.return_value = mock_client

            with pytest.raises(AIGenerationError) as excinfo:
                await generate_text("Test prompt")

            assert "exhausted retries" in str(excinfo.value).lower()
            assert mock_client.chat.completions.create.await_count == 4


async def test_generate_text_client_error_no_retry():
    with patch("app.ai.openai_client.get_ai_client") as mock_get:
        mock_client = AsyncMock()

        mock_error = APIStatusError(
            message="Invalid Key", response=MagicMock(status_code=401), body={}
        )
        mock_client.chat.completions.create.side_effect = mock_error
        mock_get.return_value = mock_client

        with pytest.raises(AIGenerationError) as excinfo:
            await generate_text("Test prompt")

        assert "401" in str(excinfo.value)
        assert mock_client.chat.completions.create.await_count == 1


async def test_generate_text_empty_response():
    """Test that an empty response from OpenAI raises AIGenerationError."""
    with patch("app.ai.openai_client.get_ai_client") as mock_get:
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content=""))]
        mock_client.chat.completions.create.return_value = mock_resp
        mock_get.return_value = mock_client

        with pytest.raises(AIGenerationError) as excinfo:
            await generate_text("Test prompt")
        assert "empty response" in str(excinfo.value).lower()


async def test_generate_text_unexpected_error():
    """Test that unexpected non-OpenAI errors are wrapped in AIGenerationError."""
    with patch("app.ai.openai_client.get_ai_client") as mock_get:
        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = RuntimeError(
            "Something went wrong"
        )
        mock_get.return_value = mock_client

        with pytest.raises(AIGenerationError) as excinfo:
            await generate_text("Test prompt")
        assert "unexpected ai failure" in str(excinfo.value).lower()
        assert "Something went wrong" in str(excinfo.value)
