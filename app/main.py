from fastapi import FastAPI
from loguru import logger

from app.api import keywords, posts, sources
from app.config import settings

logger.add(
    "logs/aibot.log",
    rotation="10 MB",  # New file every 10 mb
    retention="7 days",  # keep 7 days
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name} | {message}",
    encoding="utf-8",
)
app = FastAPI(
    title="AIBot — AI Telegram News Publisher",
    description="Service for autogeneration and publication "
    "AI posts to Telegram based on news.",
    version="0.1.0",
    debug=settings.debug,
)
app.include_router(sources.router)
app.include_router(keywords.router)
app.include_router(posts.router)
