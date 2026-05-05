from telethon import TelegramClient

from app.config import settings


def get_client() -> TelegramClient:
    return TelegramClient(
        settings.telegram_session_file,
        settings.telegram_api_id,
        str(settings.telegram_api_hash.get_secret_value()),
    )
