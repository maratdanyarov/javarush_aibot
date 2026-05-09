import asyncio
import random

from loguru import logger
from openai import APIStatusError, AsyncOpenAI, RateLimitError

from app.config import settings


class AIGenerationError(Exception):
    pass


_client: AsyncOpenAI | None = None


def get_ai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(), timeout=30.0
        )
    return _client


async def generate_text(prompt: str) -> str:
    client = get_ai_client()
    max_retries = settings.openai_max_retries
    base_delay = settings.openai_base_delay

    for attempt in range(max_retries + 1):
        try:
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.8,
            )
            content = response.choices[0].message.content
            if not content:
                raise AIGenerationError("Empty response from OpenAI")
            return content.strip()
        except (RateLimitError, APIStatusError) as e:
            if (
                isinstance(e, APIStatusError)
                and not isinstance(e, RateLimitError)
                and e.status_code < 500
            ):
                raise AIGenerationError(f"Client error {e.status_code}: {e}") from e

            if attempt == max_retries:
                raise AIGenerationError(f"OpenAI exhausted retries: {e}") from e

            wait = base_delay * (2**attempt) + random.uniform(0, 1)
            logger.warning(
                f"OpenAI error {e}. Retry {attempt + 1}/{max_retries} in {wait:.1f} s."
            )
            await asyncio.sleep(wait)

        except Exception as e:
            raise AIGenerationError(f"Unexpected AI failure: {e}") from e

    raise AIGenerationError("Retry loop exhausted unexpectedly.")
