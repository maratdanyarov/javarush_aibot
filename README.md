# AIBot — AI Telegram News Publisher

## Overview
AIBot is an automated news publishing service that parses information from various sources (RSS feeds and Telegram channels), filters it based on keywords and language, uses AI (OpenAI GPT) to generate engaging posts, and publishes them to a Telegram channel. 

The project aims to provide a hands-free solution for maintaining active and relevant Telegram communities with high-quality, AI-curated content.

## Architecture
The system follows a pipeline architecture driven by Celery tasks:

**Celery Beat** (Scheduler) 
   → `fetch_news_task`: Fetches news from enabled sources (RSS/TG) and saves to DB.
   → `filter_task`: Filters news by keywords, language, and avoids duplicates.
   → `generate_task`: Sends filtered news to OpenAI to generate post text.
   → `publish_task`: Publishes the final posts to the Telegram channel via Telethon.

- **FastAPI**: Admin API for managing sources, keywords, and monitoring posts.
- **Celery + Redis**: Task queue and scheduling.
- **SQLAlchemy + SQLite**: Data persistence for news items, posts, and configuration.
- **Telethon**: Telegram MTProto client for reading from channels and publishing.
- **OpenAI**: AI engine for text generation.

## Prerequisites
- **Python 3.12+** (if running locally)
- **Docker & Docker Compose** (recommended)
- **Redis**: Required if running locally (Docker command: `docker run -d -p 6379:6379 redis:7`)
- **Telegram Account**: API credentials (`api_id` and `api_hash`) from [my.telegram.org](https://my.telegram.org).
- **OpenAI API Key**: For post generation.
- **Telegram Channel**: Where your account has administrative permissions to post.

## Setup
1. **Clone the repository**:
   ```bash
   git clone <git@github.com:maratdanyarov/javarush_aibot.git>
   cd javarush_aibot
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Open .env and fill in your real credentials (API keys, DB URL, etc.)
   ```

3. **Initialize local environment** (For local development/testing):
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e .
   alembic upgrade head
   ```

4. **Create Telegram session**:
   Telethon requires interactive authentication the first time to create a session file. This file must exist for the Docker worker to start successfully. Run the following command locally and follow the prompts:
   ```bash
   mkdir sessions
   python3 -c "from app.telegram.client import get_client; import asyncio; asyncio.run(get_client().start())"
   ```

## Running the app

### Option A: Running with Docker (Recommended)
This is the simplest way to run the full stack (API, Redis, Worker, Beat).

**First time only — apply database migrations locally:**
```bash
alembic upgrade head
```

**Start the stack:**
```bash
docker-compose up --build
```
The services will be reachable at:
- **Admin API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs

*Note: The SQLite database (`aibot.db`) and Telegram sessions (`sessions/`) are persisted via Docker volumes.*

### Option B: Running Locally (Manual)
To run the pipeline manually, you need to start three processes in separate terminals (and ensure Redis is running):

**Terminal 1: Admin API**
```bash
uvicorn app.main:app --reload
```

**Terminal 2: Celery Worker**
```bash
celery -A celery_worker worker --loglevel=info
```

**Terminal 3: Celery Beat (Scheduler)**
```bash
celery -A celery_worker beat --loglevel=info
```

## API Reference (curl examples)

### 1. Create a new source
```bash
curl -X POST http://localhost:8000/sources \
     -H "Content-Type: application/json" \
     -d '{"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "type": "site"}'
```

### 2. Trigger manual post generation
```bash
curl -X POST http://localhost:8000/api/generate \
     -H "Content-Type: application/json" \
     -d '{"news_item_id": "uuid-of-the-news-item"}'
```

### 3. View post history (with status filter)
```bash
curl "http://localhost:8000/posts?status=published&limit=10"
```

## Environment variables

| Variable | Required | Description                                                           |
| :--- | :--- |:----------------------------------------------------------------------|
| `DATABASE_URL` | Yes | SQLAlchemy connection string (e.g., `sqlite+aiosqlite:///./aibot.db`) |
| `REDIS_URL` | Yes | Redis broker URL (e.g., `redis://localhost:6379/0`)                   |
| `TELEGRAM_API_ID` | Yes | Your Telegram API ID                                                  |
| `TELEGRAM_API_HASH` | Yes | Your Telegram API Hash                                                |
| `TG_CHANNEL` | Yes | Target channel username (e.g., `@my_news_channel`)                    |
| `TELEGRAM_SESSION_FILE` | Yes | Path to Telethon session file (e.g., `sessions/aibot`)                |
| `OPENAI_API_KEY` | Yes | Your OpenAI API Key                                                   |
| `OPENAI_MODEL` | No | OpenAI model to use (default: `gpt-4o-mini`)                          |
| `DEBUG` | No | Enable debug mode (default: `False`)                                  |
| `LOG_LEVEL` | No | Logging level (INFO, DEBUG, ERROR)                                    |
| `OPENAI_MAX_RETRIES` | No | Max retries for OpenAI API (default: `3`)                             |
| `OPENAI_BASE_DELAY` | No | Base delay for exponential backoff (default: `1.0`)                   |
| `ALLOWED_LANGUAGES` | No | List of allowed languages (default: `["en", "ru", "kz"]`)             |

## Implemented features checklist
- [x] **E1 — Project Skeleton**: Configuration, Ruff/Pyright, structure.
- [x] **E2 — Data Layer**: SQLAlchemy models, Alembic migrations, Pydantic schemas.
- [x] **E3 — Admin API**: CRUD for sources, keywords, and post history.
- [x] **E4 — Site Parser**: Async RSS/HTML parsing with BeautifulSoup.
- [x] **E5 — Celery Infrastructure**: Task chaining, background processing, scheduling.
- [x] **E6 — Telegram Parser**: Telethon integration for fetching via MTProto.
- [x] **E7 — Filtering & Deduplication**: Keyword matching, language detection, hash-based dedup.
- [x] **E8 — AI Generation**: OpenAI client with retries and post formatting.
- [x] **E9 — Publisher**: Idempotent Telegram publication via Telethon.
- [x] **E10 — Wiring**: Full end-to-end Celery chain and integration tests.
- [x] **E11 — Polish**: Final documentation and Docker support.
