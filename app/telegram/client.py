"""Telethon TelegramClient factory using the persisted MTProto session file."""

from telethon import TelegramClient

from app.config import settings


def get_client() -> TelegramClient:
    """Return a TelegramClient configured with the persisted session file and API credentials."""
    return TelegramClient(
        settings.telegram_session_file,
        settings.telegram_api_id,
        str(settings.telegram_api_hash.get_secret_value()),
    )
