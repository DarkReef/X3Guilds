from pathlib import Path

import pytest

from x3guilds_ai.bridge import encode_chat_request, encode_context_selection
from x3guilds_ai.file_bridge import FileBridge
from x3guilds_ai.memory import SQLiteMemoryStore
from x3guilds_ai.models import ChatRequest, ContextSelection, EntityContext
from x3guilds_ai.providers.mock import MockDialogueProvider
from x3guilds_ai.service import ChatService


def entity() -> EntityContext:
    return EntityContext(entity_id="bridge", name="Pilot", kind="ship")


async def make_bridge(tmp_path: Path, **kwargs) -> FileBridge:
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite3")
    service = ChatService(provider=MockDialogueProvider(), memory=memory)
    await service.initialize()
    return FileBridge(
        request_path=tmp_path / "log09980.txt",
        response_path=tmp_path / "responses.log",
        checkpoint_path=tmp_path / "checkpoint.json",
        diagnostics_path=tmp_path / "diagnostics",
        service=service,
        **kwargs,
    )


@pytest.mark.asyncio
async def test_bridge_checkpoints_and_does_not_repeat(tmp_path: Path) -> None:
    seen = []

    async def callback(req, result):
        seen.append((req, result))

    bridge = await make_bridge(tmp_path, callback=callback)
    request = ChatRequest(
        request_id="req-bridge",
        conversation_id="npc:bridge",
        message="status",
        entity=entity(),
    )
    bridge.request_path.write_text("other line\n" + encode_chat_request(request) + "\n", encoding="utf-8")
    assert await bridge.run_once() == 1
    assert await bridge.run_once() == 0
    assert bridge.response_path.read_text(encoding="utf-8").count("CHAT_RESPONSE") == 1
    assert len(seen) == 1


@pytest.mark.asyncio
async def test_append_does_not_replay_short_file(tmp_path: Path) -> None:
    bridge = await make_bridge(tmp_path)
    one = ChatRequest(
        request_id="req-one-1",
        conversation_id="npc:bridge",
        message="one",
        entity=entity(),
    )
    two = one.model_copy(update={"request_id": "req-two-2", "message": "two"})
    bridge.request_path.write_text(encode_chat_request(one) + "\n", encoding="utf-8")
    assert await bridge.run_once() == 1
    with bridge.request_path.open("a", encoding="utf-8") as handle:
        handle.write(encode_chat_request(two) + "\n")
    assert await bridge.run_once() == 1
    assert bridge.response_path.read_text(encoding="utf-8").count("CHAT_RESPONSE") == 2


@pytest.mark.asyncio
async def test_bridge_reports_context_without_calling_model(tmp_path: Path) -> None:
    contexts = []
    bridge = await make_bridge(tmp_path, context_callback=contexts.append)
    context = ContextSelection(context_id="ctx-1", entity=entity(), game_time=10)
    bridge.request_path.write_text(encode_context_selection(context) + "\n", encoding="utf-8")
    assert await bridge.run_once() == 1
    assert contexts == [context]
    assert not bridge.response_path.exists()


@pytest.mark.asyncio
async def test_bridge_recovers_after_log_truncation(tmp_path: Path) -> None:
    bridge = await make_bridge(tmp_path)
    one = ChatRequest(
        request_id="req-one-1",
        conversation_id="npc:bridge",
        message="one",
        entity=entity(),
    )
    two = one.model_copy(update={"request_id": "req-two-2", "message": "two"})
    bridge.request_path.write_text(encode_chat_request(one) + "\n", encoding="utf-8")
    assert await bridge.run_once() == 1
    bridge.request_path.write_text(encode_chat_request(two) + "\n", encoding="utf-8")
    assert await bridge.run_once() == 1
