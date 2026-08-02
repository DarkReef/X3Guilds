from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path

from x3guilds_ai.bridge import encode_chat_response, parse_chat_request
from x3guilds_ai.service import ChatService


@dataclass(slots=True)
class BridgeCheckpoint:
    offset: int = 0


class FileBridge:
    """Incrementally consumes XUGC lines from an X3 log file."""

    def __init__(
        self,
        *,
        service: ChatService,
        input_path: Path,
        output_path: Path,
        checkpoint_path: Path,
    ) -> None:
        self._service = service
        self._input_path = input_path
        self._output_path = output_path
        self._checkpoint_path = checkpoint_path

    def _load_checkpoint(self) -> BridgeCheckpoint:
        try:
            payload = json.loads(self._checkpoint_path.read_text(encoding="utf-8"))
            return BridgeCheckpoint(offset=max(0, int(payload.get("offset", 0))))
        except (FileNotFoundError, ValueError, TypeError, json.JSONDecodeError):
            return BridgeCheckpoint()

    def _save_checkpoint(self, checkpoint: BridgeCheckpoint) -> None:
        self._checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._checkpoint_path.with_suffix(self._checkpoint_path.suffix + ".tmp")
        temporary.write_text(json.dumps({"offset": checkpoint.offset}), encoding="utf-8")
        os.replace(temporary, self._checkpoint_path)

    def _read_available(self, offset: int) -> tuple[list[str], int]:
        if not self._input_path.exists():
            return [], 0
        size = self._input_path.stat().st_size
        if size < offset:
            offset = 0
        with self._input_path.open("r", encoding="utf-8", errors="replace") as stream:
            stream.seek(offset)
            lines = stream.readlines()
            new_offset = stream.tell()
        return lines, new_offset

    def _append_output(self, line: str) -> None:
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        with self._output_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(line.rstrip("\r\n") + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    async def process_available(self) -> int:
        checkpoint = self._load_checkpoint()
        lines, new_offset = await asyncio.to_thread(self._read_available, checkpoint.offset)
        processed = 0
        for line in lines:
            if not line.startswith("XUGC|"):
                continue
            try:
                request = parse_chat_request(line)
                response = await self._service.chat(request)
                await asyncio.to_thread(self._append_output, encode_chat_response(response))
                processed += 1
            except ValueError:
                continue
        checkpoint.offset = new_offset
        await asyncio.to_thread(self._save_checkpoint, checkpoint)
        return processed

    async def run_forever(self, poll_interval: float = 0.5) -> None:
        if poll_interval < 0.1:
            raise ValueError("poll_interval must be at least 0.1 seconds")
        while True:
            await self.process_available()
            await asyncio.sleep(poll_interval)
