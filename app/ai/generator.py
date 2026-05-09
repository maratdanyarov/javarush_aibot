from app.ai.openai_client import generate_text
from app.models import NewsItem

PROMPT = """Ты — редактор новостного Telegram-канала.  
Твоя задача — писать короткие, живые и интересные посты на основе новостей.  

Правила:  
1. Длина поста: 3–5 предложений, максимум 900 символов.  
2. Начинай с самого важного — без воды.  
3. Добавляй 2–3 релевантных emoji.  
4. В конце — короткий call to action или вопрос к читателю.  
5. Пиши на том же языке, что и исходная новость.  
6. Не используй markdown — только чистый текст для Telegram.  
7. Не придумывай факты — только то, что есть в источнике.

Напиши Telegram-пост на основе этой новости:  

Заголовок: {title}  
Источник: {source}  
Текст: {summary}  

Напиши только текст поста, без объяснений."""


async def generate_post(item: NewsItem) -> str:
    prompt = PROMPT.format(
        title=item.title, source=item.source, summary=item.summary[:1500]
    )

    return await generate_text(prompt)
