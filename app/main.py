from fastapi import FastAPI

from app.api.endpoints import router
from app.config import settings
app = FastAPI(
    title="AIBot — AI Telegram News Publisher",
    description="Service for autogeneration and publication AI posts to Telegram based on news.",
    version="0.1.0",
    debug=settings.debug
)
app.include_router(router)
