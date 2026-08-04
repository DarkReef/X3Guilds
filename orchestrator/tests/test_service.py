import asyncio
from pathlib import Path

import pytest

from x3guilds_ai.memory import RequestIdConflictError, SQLiteMemoryStore
from x3guilds_ai.models import ChatRequest, EntityContext, ModelDialogue
from x3guilds_ai.providers.mock import MockDialogueProvider
from x3guilds_ai.service import ChatService


def request(message: str = "Привет") -> ChatRequest:
    return ChatRequest(
        request_id="request-1",
        conversation_id="npc:1",
        message=message,
        entity=EntityContext(entity_id="1", name="Pilot", kind="ship"),
    )


class CountingProvider:
    name = "counting"

    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, request, history, memories) -> ModelDialogue:
        self.calls += 1
        await asyncio.sleep(0)
        return ModelDialogue(
            reply=f"Ответ: {request.message}",
            mood="neutral",
            memories=[],
            actions=[],
        )


@pytest.mark.asyncio
async def test_idempotency_and_memory(tmp_path: Path) -> None:
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite3")
    service = ChatService(provider=MockDialogueProvider(), memory=memory)
    await service.initialize()

    first = await service.chat(request())
    second = await service.chat(request())
    assert first.cached is False
    assert second.cached is True
    facts = await memory.memories("npc:1", 10)
    assert facts == ["Игрок сказал: Привет"]


@pytest.mark.asyncio
async def test_duplicate_id_with_other_payload_is_rejected(tmp_path: Path) -> None:
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite3")
    service = ChatService(provider=MockDialogueProvider(), memory=memory)
    await service.initialize()
    await service.chat(request("one"))
    with pytest.raises(RequestIdConflictError):
        await service.chat(request("two"))


@pytest.mark.asyncio
async def test_concurrent_duplicate_calls_generate_once(tmp_path: Path) -> None:
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite3")
    provider = CountingProvider()
    service = ChatService(provider=provider, memory=memory)
    await service.initialize()

    first, second = await asyncio.gather(
        service.chat(request()),
        service.chat(request()),
    )

    assert provider.calls == 1
    assert {first.cached, second.cached} == {False, True}
    history = await memory.recent("npc:1", 10)
    assert len(history) == 2
