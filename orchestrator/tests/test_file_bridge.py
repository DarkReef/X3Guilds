from pathlib import Path
from urllib.parse import quote

import pytest

from x3guilds_ai.file_bridge import FileBridge
from x3guilds_ai.memory import SQLiteMemoryStore
from x3guilds_ai.providers.mock import MockDialogueProvider
from x3guilds_ai.service import ChatService


def e(value: str) -> str:
    return quote(value, safe="")


def request_line(request_id: str) -> str:
    return "|".join(
        [
            "XUGC",
            "1",
            "CHAT_REQUEST",
            e(request_id),
            e("conversation-7"),
            e("ship-42"),
            e("Капитан Хаалас"),
            "ship",
            e("Телади"),
            e("PTNI"),
            e("Profit Center Alpha"),
            "23",
            "18443300",
            e("Назовите вашу цену."),
        ]
    )


@pytest.mark.asyncio
async def test_bridge_tails_only_new_lines(tmp_path: Path) -> None:
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite3")
    service = ChatService(provider=MockDialogueProvider(), memory=memory)
    await service.initialize()
    input_path = tmp_path / "log09980.txt"
    output_path = tmp_path / "outbox.log"
    bridge = FileBridge(
        service=service,
        input_path=input_path,
        output_path=output_path,
        checkpoint_path=tmp_path / "checkpoint.json",
    )

    input_path.write_text("noise\n" + request_line("request-0001") + "\n", encoding="utf-8")
    assert await bridge.process_available() == 1
    assert await bridge.process_available() == 0

    with input_path.open("a", encoding="utf-8") as stream:
        stream.write(request_line("request-0002") + "\n")
    assert await bridge.process_available() == 1

    responses = output_path.read_text(encoding="utf-8").splitlines()
    assert len(responses) == 2
    assert responses[0].startswith("XUGC|1|CHAT_RESPONSE|request-0001|")
    assert responses[1].startswith("XUGC|1|CHAT_RESPONSE|request-0002|")
