from __future__ import annotations

from x3guilds_ai.config import Settings
from x3guilds_ai.memory import SQLiteMemoryStore
from x3guilds_ai.providers.base import DialogueProvider
from x3guilds_ai.providers.gigachat import GigaChatProvider
from x3guilds_ai.providers.mock import MockDialogueProvider
from x3guilds_ai.service import ChatService


def create_provider(settings: Settings) -> DialogueProvider:
    if settings.provider == "mock":
        return MockDialogueProvider()
    if settings.provider == "gigachat":
        if not settings.gigachat_credentials:
            raise ValueError(
                "X3AI_GIGACHAT_CREDENTIALS is required when X3AI_PROVIDER=gigachat"
            )
        return GigaChatProvider(
            credentials=settings.gigachat_credentials,
            scope=settings.gigachat_scope,
            model=settings.gigachat_model,
            base_url=settings.gigachat_base_url,
            oauth_url=settings.gigachat_oauth_url,
            verify_ssl=settings.gigachat_verify_ssl,
            timeout=settings.gigachat_timeout_seconds,
            retries=settings.gigachat_retries,
        )
    raise ValueError(f"Unknown X3AI_PROVIDER: {settings.provider}")


def create_service(settings: Settings) -> ChatService:
    return ChatService(
        provider=create_provider(settings),
        memory=SQLiteMemoryStore(settings.database_path),
        history_limit=settings.history_limit,
        memory_limit=settings.memory_limit,
    )
