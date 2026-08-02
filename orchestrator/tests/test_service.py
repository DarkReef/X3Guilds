from pathlib import Path

import pytest

from x3guilds_ai.memory import SQLiteMemoryStore
from x3guilds_ai.models import ChatRequest, EntityContext
from x3guilds_ai.providers.mock import MockDialogueProvider
from x3guilds_ai.service import ChatService


@pytest.mark.asyncio
async def test_chat_is_persisted_and_idempotent(tmp_path: Path) -> None:
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite3")
    await memory.initialize()
    service = ChatService(provider=MockDialogueProvider(), memory=memory)
    request = ChatRequest(
        request_id="request-0001",
        conversation_id="captain-1",
        message="Что происходит в секторе?",
        entity=EntityContext(
            entity_id="ship-42",
            name="Капитан Хаалас",
            kind="ship",
            race="Телади",
            faction="PTNI",
            sector="Profit Center Alpha",
        ),
    )

    first = await service.chat(request)
    second = await service.chat(request)

    assert first.cached is False
    assert second.cached is True
    assert second.reply == first.reply
    history = await memory.recent("captain-1", 10)
    assert [item.role for item in history] == ["user", "assistant"]
